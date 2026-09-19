"""Failures that mean 'try another way in' rather than 'give up'."""


class IngestError(RuntimeError):
    """The source could not be turned into a transcript."""


class TranscriptUnavailable(IngestError):
    """No usable captions - speech recognition is the remaining option."""
