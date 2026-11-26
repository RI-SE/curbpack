"""Sentences shown with a review. They are not stored on the report."""

NOT_A_LEGAL_CONCLUSION = "A passing check does not mean the legal requirement is fulfilled."
NO_CRA_FIELD = "This report has no field for a conclusion that the product meets CRA."


def worktree_sentence(run_result: dict) -> str:
    """Page copy. It is not stored on the report."""
    if not isinstance(run_result, dict):
        return ""
    if run_result.get("worktree") == "dirty":
        return "This result is not verification of that commit's content."
    if run_result.get("worktree") == "clean":
        return "The worktree was clean."
    return ""
