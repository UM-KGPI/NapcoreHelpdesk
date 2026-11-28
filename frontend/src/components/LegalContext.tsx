/**
 * "Legal context" line under an answer: the provisions of the EU acts that name the standard the answer
 * is about (e.g. MMTIS Art. 4 for NeTEx), linked to EUR-Lex. Renders nothing when there are none.
 */
import type { LegalContextItem } from "../types";

export default function LegalContext({ items }: { items?: LegalContextItem[] }) {
  if (!items || items.length === 0) {
    return null;
  }
  return (
    <p className="tiny legal-context">
      <strong>Legal context:</strong>{" "}
      {items.map((item, index) => (
        <span key={item.url}>
          {index > 0 && " · "}
          <a href={item.url} target="_blank" rel="noreferrer">
            {item.label}
          </a>
        </span>
      ))}
    </p>
  );
}
