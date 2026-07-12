// Helpers to render citation entries consistently with the [E#] markers in
// LLM answer text. The backend labels LLM citations "E1".."EN" mirroring the
// prompt's evidence numbering; older events and non-LLM answers have no such
// label, so the list position is the only (best-effort) fallback.

const EVIDENCE_LABEL_PATTERN = /^E\d+$/;

interface CitationLike {
  label?: string | null;
  sourcePath: string;
}

/** Marker shown before a citation entry, e.g. "[E2]" — matches the answer text. */
export function citationMarker(citation: CitationLike, index: number): string {
  const label = citation.label ?? "";
  return EVIDENCE_LABEL_PATTERN.test(label) ? `[${label}]` : `[E${index + 1}]`;
}

/** Human-readable name for a citation entry (never the E# marker itself). */
export function citationDisplayName(citation: CitationLike): string {
  const label = citation.label ?? "";
  if (label && !EVIDENCE_LABEL_PATTERN.test(label) && label !== citation.sourcePath) {
    return label;
  }
  return citation.sourcePath.split("/").pop() ?? citation.sourcePath;
}
