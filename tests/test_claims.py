from truthcast.models import ClaimKind
from truthcast.pipeline.claims import ClaimDraft, rank_and_dedupe


def draft(text, **kwargs):
    return ClaimDraft(text=text, quote=kwargs.pop("quote", "said it"), **kwargs)


def test_opinions_and_predictions_never_reach_research():
    claims = rank_and_dedupe(
        [
            draft("Jazz is the best music", kind=ClaimKind.OPINION, importance=0.9),
            draft("AI will replace doctors by 2030", kind=ClaimKind.PREDICTION, importance=0.9),
            draft("Coffee prices rose 30 percent in 2024", importance=0.5),
        ],
        limit=10,
    )
    assert [c.text for c in claims] == ["Coffee prices rose 30 percent in 2024"]


def test_restatements_of_the_same_claim_collapse():
    claims = rank_and_dedupe(
        [
            draft("The Amazon produces 20 percent of Earth's oxygen", importance=0.9),
            draft("20 percent of Earth's oxygen is produced by the Amazon", importance=0.4),
        ],
        limit=10,
    )
    assert len(claims) == 1
    assert claims[0].importance == 0.9  # the stronger framing survives


def test_most_consequential_claims_come_first_and_the_limit_holds():
    claims = rank_and_dedupe(
        [
            draft("Zinc lozenges shorten colds", importance=0.4),
            draft("This drug interaction can stop your heart", importance=0.95),
            draft("Venus rotates backwards", importance=0.2),
        ],
        limit=2,
    )
    assert len(claims) == 2
    assert claims[0].text.startswith("This drug interaction")


def test_ids_stay_dense_after_filtering():
    claims = rank_and_dedupe(
        [
            draft("Opinion one", kind=ClaimKind.OPINION),
            draft("Sea levels rose 20 centimetres since 1900"),
            draft("The moon is drifting away from Earth"),
        ],
        limit=10,
    )
    assert [c.id for c in claims] == ["c1", "c2"]


def test_timestamps_are_parsed_from_the_transcript_marker():
    claims = rank_and_dedupe([draft("Sleep matters", said_at="12:04")], limit=5)
    assert claims[0].start_seconds == 724.0


def test_empty_input_is_fine():
    assert rank_and_dedupe([], limit=5) == []


def test_claims_differing_only_in_a_number_are_not_duplicates():
    # Fingerprints must keep digits, or "rose 30%" and "rose 50%" would merge
    # and one of two contradictory claims would silently vanish.
    claims = rank_and_dedupe(
        [
            draft("Coffee prices rose 30 percent in 2024", importance=0.9),
            draft("Coffee prices rose 50 percent in 2024", importance=0.8),
        ],
        limit=10,
    )
    assert len(claims) == 2
