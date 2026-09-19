"""Thin async wrapper over the Claude API.

Two shapes are used by the pipeline:

* ``structured`` - ask for one validated Pydantic object back.
* ``research``   - let Claude run the server-side web_search tool and return
  both what it wrote and every source it actually opened.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel

from .config import Settings, get_settings

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Dynamic-filtering variant; supported on Opus 5 / 4.8 / 4.7 / 4.6 and Sonnet 5 / 4.6.
WEB_SEARCH_TOOL = "web_search_20260209"
MAX_PAUSE_RESUMES = 4


class LLMError(RuntimeError):
    """The model could not be used for this step."""


class RefusalError(LLMError):
    """Safety classifiers declined the request."""


@dataclass
class SearchHit:
    url: str
    title: str = ""
    snippet: str = ""
    published: str | None = None


@dataclass
class ResearchResult:
    text: str
    hits: list[SearchHit] = field(default_factory=list)
    searches: int = 0


class ClaudeClient:
    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                self._client = anthropic.AsyncAnthropic()
            except Exception as exc:  # missing credentials surface here, once
                raise LLMError(
                    "No Claude credentials found. Set ANTHROPIC_API_KEY or run `ant auth login`."
                ) from exc
        return self._client

    # ------------------------------------------------------------------ #

    async def structured(
        self,
        *,
        system: str,
        user: str,
        output_model: type[T],
        model: str | None = None,
        effort: str | None = None,
        max_tokens: int = 16_000,
    ) -> T:
        """One request, one validated object."""
        try:
            response = await self.client.messages.parse(
                model=model or self.settings.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=output_model,
                thinking={"type": "adaptive"},
                output_config={"effort": effort or self.settings.effort},
            )
        except anthropic.APIStatusError as exc:
            raise LLMError(f"Claude API error ({exc.status_code}): {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            raise LLMError(f"Could not reach the Claude API: {exc}") from exc

        _guard_stop_reason(response)
        parsed = getattr(response, "parsed_output", None)
        if parsed is None:
            raise LLMError("Model returned no structured output.")
        return parsed

    async def research(
        self,
        *,
        system: str,
        user: str,
        max_uses: int | None = None,
        max_tokens: int = 8_000,
    ) -> ResearchResult:
        """Let Claude search the live web, and report back what it read."""
        tools = [
            {
                "type": WEB_SEARCH_TOOL,
                "name": "web_search",
                "max_uses": max_uses or self.settings.max_searches_per_claim,
            }
        ]
        messages: list[dict[str, Any]] = [{"role": "user", "content": user}]
        chunks: list[str] = []
        hits: list[SearchHit] = []
        searches = 0

        for _ in range(MAX_PAUSE_RESUMES + 1):
            try:
                async with self.client.messages.stream(
                    model=self.settings.model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=messages,
                    tools=tools,
                    thinking={"type": "adaptive"},
                    output_config={"effort": self.settings.effort},
                ) as stream:
                    response = await stream.get_final_message()
            except anthropic.APIStatusError as exc:
                raise LLMError(f"Claude API error ({exc.status_code}): {exc.message}") from exc
            except anthropic.APIConnectionError as exc:
                raise LLMError(f"Could not reach the Claude API: {exc}") from exc

            _guard_stop_reason(response)
            text, found, used = harvest_blocks(response.content)
            chunks.append(text)
            hits.extend(found)
            searches += used

            if response.stop_reason != "pause_turn":
                break
            # The turn is mid-flight: hand it straight back so Claude continues.
            messages.append({"role": "assistant", "content": response.content})
        else:
            log.warning("web search turn still paused after %s resumes", MAX_PAUSE_RESUMES)

        return ResearchResult(
            text="\n".join(c for c in chunks if c).strip(),
            hits=dedupe_hits(hits),
            searches=searches,
        )


def _guard_stop_reason(response: Any) -> None:
    if getattr(response, "stop_reason", None) == "refusal":
        details = getattr(response, "stop_details", None)
        category = getattr(details, "category", None) or "unspecified"
        raise RefusalError(f"Claude declined this request (category: {category}).")


def harvest_blocks(blocks: Any) -> tuple[str, list[SearchHit], int]:
    """Pull the prose, the search results and the search count out of a response.

    Server-tool failures come back as a *result block whose content is an error
    object* rather than a list - and never as an exception - so both shapes are
    handled here.
    """
    text_parts: list[str] = []
    hits: list[SearchHit] = []
    searches = 0

    for block in blocks or []:
        btype = _get(block, "type")
        if btype == "text":
            text_parts.append(_get(block, "text") or "")
            for citation in _get(block, "citations") or []:
                url = _get(citation, "url")
                if url:
                    hits.append(
                        SearchHit(
                            url=url,
                            title=_get(citation, "title") or "",
                            snippet=_get(citation, "cited_text") or "",
                        )
                    )
        elif btype == "web_search_tool_result":
            searches += 1
            content = _get(block, "content")
            if not isinstance(content, list):
                code = _get(content, "error_code") or "unknown"
                log.warning("web search failed: %s", code)
                continue
            for result in content:
                url = _get(result, "url")
                if not url:
                    continue
                hits.append(
                    SearchHit(
                        url=url,
                        title=_get(result, "title") or "",
                        snippet=(_get(result, "snippet") or "")[:600],
                        published=_get(result, "page_age"),
                    )
                )

    return "\n".join(p for p in text_parts if p).strip(), hits, searches


def dedupe_hits(hits: list[SearchHit]) -> list[SearchHit]:
    """Keep first sighting of each URL, preferring the entry that carries a snippet."""
    by_url: dict[str, SearchHit] = {}
    for hit in hits:
        existing = by_url.get(hit.url)
        if existing is None:
            by_url[hit.url] = hit
        elif not existing.snippet and hit.snippet:
            existing.snippet = hit.snippet
        elif not existing.title and hit.title:
            existing.title = hit.title
    return list(by_url.values())


def _get(obj: Any, name: str) -> Any:
    """Read a field from an SDK model or a plain dict."""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)
