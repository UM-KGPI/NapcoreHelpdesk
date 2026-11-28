// Helpers to render citation entries consistently with the [E#] markers in
// LLM answer text. The backend labels LLM citations "E1".."EN" mirroring the
// prompt's evidence numbering; older events and non-LLM answers have no such
// label, so the list position is the only (best-effort) fallback.

const EVIDENCE_LABEL_PATTERN = /^E\d+$/;

interface CitationLike {
  label?: string | null;
  sourcePath: string;
  /** Readable name of a cited part of an EU act ("MMTIS Art. 4"), when the backend sends one. */
  title?: string;
}

/** Marker shown before a citation entry, e.g. "[E2]" — matches the answer text. */
export function citationMarker(citation: CitationLike, index: number): string {
  const label = citation.label ?? "";
  return EVIDENCE_LABEL_PATTERN.test(label) ? `[${label}]` : `[E${index + 1}]`;
}

/** Human-readable name for a citation entry (never the E# marker itself). */
export function citationDisplayName(citation: CitationLike): string {
  if (citation.title) {
    return citation.title;
  }
  const label = citation.label ?? "";
  if (label && !EVIDENCE_LABEL_PATTERN.test(label) && label !== citation.sourcePath) {
    return label;
  }
  return citation.sourcePath.split("/").pop() ?? citation.sourcePath;
}

export interface CitationGroup<T extends CitationLike> {
  /** All entries sharing the same sourcePath, in original list order. */
  citations: T[];
  /** Markers for each entry, e.g. ["[E1]", "[E2]"] — order matches `citations`. */
  markers: string[];
  /** First entry of the group; use for the link target and display name. */
  primary: T;
}

/**
 * Group citations that reference the same source file so the evidence list
 * shows one row per document with all its E# markers, instead of repeating
 * the file once per cited chunk. Markers keep their original list positions
 * so they still match the [E#] references in the answer text.
 */
export function groupCitationsBySource<T extends CitationLike>(citations: T[]): CitationGroup<T>[] {
  const groups: CitationGroup<T>[] = [];
  const byPath = new Map<string, CitationGroup<T>>();
  citations.forEach((citation, index) => {
    let group = byPath.get(citation.sourcePath);
    if (!group) {
      group = { citations: [], markers: [], primary: citation };
      byPath.set(citation.sourcePath, group);
      groups.push(group);
    }
    group.citations.push(citation);
    group.markers.push(citationMarker(citation, index));
  });
  return groups;
}
