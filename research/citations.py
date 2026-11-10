"""Reference/quote checks; never label these as factual verification."""

import re
from urllib.parse import quote as urlquote

from research.models import Finding, GroundedAnswer, Passage


def normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def check_answer(answer: GroundedAnswer, passages: list[Passage]) -> tuple[GroundedAnswer, int]:
    lookup = {p.id: p for p in passages}
    accepted: list[Finding] = []
    for finding in answer.findings:
        if all(
            e.passage_id in lookup and normalize(e.quote) in normalize(lookup[e.passage_id].text)
            for e in finding.evidence
        ):
            accepted.append(finding)
    rejected = len(answer.findings) - len(accepted)
    limitations = list(answer.limitations)
    if rejected:
        limitations.append(
            f"Removed {rejected} finding(s) with unknown references or non-matching quotes."
        )
    if answer.insufficient_evidence:
        accepted = []
    return GroundedAnswer(
        findings=accepted, limitations=limitations, insufficient_evidence=not accepted
    ), rejected


def plain_markdown(text: str) -> str:
    return re.sub(r"([\\`*_{}\[\]()<>#!|])", r"\\\1", text.replace("\n", " "))


def render_report(
    query: str, answer: GroundedAnswer, passages: list[Passage], *, demo: bool = False
) -> str:
    lookup = {p.id: p for p in passages}
    lines = [f"# {plain_markdown(query)}", ""]
    if demo:
        lines += ["> Extractive demo: source excerpts only; no AI synthesis.", ""]
    if answer.insufficient_evidence:
        lines += [
            "## Evidence insufficient",
            "The retrieved evidence does not support a reliable answer. Try a narrower question or provide better sources.",
            "",
        ]
    else:
        lines += ["## Findings", ""]
        for finding in answer.findings:
            references = " ".join(
                f"[{e.passage_id}]({urlquote(lookup[e.passage_id].url, safe=':/?=&%#-._~')})"
                for e in finding.evidence
            )
            lines += [f"- {plain_markdown(finding.claim)} {references}"]
    lines += ["", "## Evidence excerpts", ""]
    seen: set[tuple[str, str]] = set()
    for finding in answer.findings:
        for evidence in finding.evidence:
            key = (evidence.passage_id, evidence.quote)
            if key in seen:
                continue
            seen.add(key)
            p = lookup[evidence.passage_id]
            lines += [
                f"**{p.id} — {plain_markdown(p.title)}**",
                f"> {plain_markdown(evidence.quote)}",
                "",
            ]
    lines += [
        "## Limitations",
        "",
        "- Citation IDs and quoted text were checked against retrieved passages. This does not independently verify whether every claim follows from its evidence.",
    ]
    lines += [f"- {plain_markdown(item)}" for item in answer.limitations]
    return "\n".join(lines)
