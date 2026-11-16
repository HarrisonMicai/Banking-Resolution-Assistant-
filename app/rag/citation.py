
"""
Citation formatting and validation for grounded RAG answers.

Only citations matching retrieved evidence are accepted.
"""

def _get_evidence_metadata(evidence):
    """Extract metadata from a retrieval result."""

    metadata = evidence.get("metadata", evidence)

    return {
        "source_id": metadata.get("source_id"),
        "title": metadata.get("title"),
        "section": (
            metadata.get("section_title")
            or metadata.get("section")
        ),
        "version": metadata.get("version")
    }


def format_citations(citation_candidates, retrieved_evidence):
    """
    Validate model-generated citation candidates against
    the actual retrieved evidence.

    Returns canonical citation dictionaries using metadata
    from retrieved evidence, not model-generated metadata.

    Raises ValueError if a citation cannot be verified.
    """

    if not isinstance(citation_candidates, list):
        raise ValueError("Citations must be provided as a list.")

    if not isinstance(retrieved_evidence, list):
        raise ValueError("Retrieved evidence must be a list.")

    # Build an index of citations that actually exist.
    evidence_index = {}

    for evidence in retrieved_evidence:
        metadata = _get_evidence_metadata(evidence)

        source_id = metadata["source_id"]
        section = metadata["section"]

        if not source_id or not section:
            continue

        evidence_index[(source_id, section)] = metadata

    validated_citations = []
    seen = set()

    for candidate in citation_candidates:

        if not isinstance(candidate, dict):
            raise ValueError("Each citation must be an object.")

        source_id = candidate.get("source_id")
        section = candidate.get("section")

        if not source_id or not section:
            raise ValueError(
                "Citation must include source_id and section."
            )

        citation_key = (source_id, section)

        # Reject citations absent from retrieved evidence.
        if citation_key not in evidence_index:
            raise ValueError(
                f"Unverified citation rejected: "
                f"{source_id} - {section}"
            )

        if citation_key in seen:
            continue

        evidence_metadata = evidence_index[citation_key]

        # Require complete metadata for a verifiable citation.
        if not all([
            evidence_metadata["title"],
            evidence_metadata["version"]
        ]):
            raise ValueError(
                f"Incomplete citation metadata for {source_id}."
            )

        # Use the retrieved metadata, never model-supplied values.
        validated_citations.append({
            "source_id": evidence_metadata["source_id"],
            "title": evidence_metadata["title"],
            "section": evidence_metadata["section"],
            "version": str(evidence_metadata["version"])
        })

        seen.add(citation_key)

    return validated_citations


def render_citation(citation):
    """Render a validated citation as readable text."""

    required_fields = [
        "source_id",
        "title",
        "section",
        "version"
    ]

    if not all(citation.get(field) for field in required_fields):
        raise ValueError("Cannot render an incomplete citation.")

    return (
        f"{citation['title']} | "
        f"{citation['section']} | "
        f"Version {citation['version']} | "
        f"Source ID: {citation['source_id']}"
    )
