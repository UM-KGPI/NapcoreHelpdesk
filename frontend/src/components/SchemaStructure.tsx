/**
 * What an element contains according to the NeTEx schema, shown first for "what does X contain" questions:
 * the element's own child elements, then those inherited from each base type (collapsed), then its
 * attributes, each with the schema's own definition. Taken from the XSD index, no model involved.
 */
import type { SchemaStructure } from "../types";

function Definitions({ items }: { items: { name: string; documentation: string }[] }) {
  return (
    <dl>
      {items.map((item) => (
        <div key={item.name}>
          <dt>
            <code>{item.name}</code>
          </dt>
          <dd>{item.documentation || <span className="muted">(no definition in the schema)</span>}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function SchemaStructureBlock({ structure }: { structure?: SchemaStructure | null }) {
  if (!structure) {
    return null;
  }
  const own = structure.groups.filter((group) => !group.inherited);
  const inherited = structure.groups.filter((group) => group.inherited);
  const total = structure.groups.reduce((sum, group) => sum + group.children.length, 0);
  return (
    <section className="schema-structure" aria-label={`What ${structure.element} contains`}>
      <h4>
        What <code>{structure.element}</code> contains
      </h4>
      <p className="tiny schema-structure-badge">
        From the NeTEx schema{structure.source ? ` · ${structure.source}` : ""} · {total} child elements ·{" "}
        {structure.attributes.length} attributes
      </p>
      {structure.documentation ? <p>{structure.documentation}</p> : null}
      {own.map((group) => (
        <div key={group.owner}>
          <p className="tiny">
            <strong>Its own elements</strong>
          </p>
          <Definitions items={group.children} />
        </div>
      ))}
      {inherited.map((group) => (
        <details key={group.owner}>
          <summary className="tiny">
            Inherited as <code>{group.owner}</code> ({group.children.length})
          </summary>
          <Definitions items={group.children} />
        </details>
      ))}
      {structure.attributes.length > 0 ? (
        <details>
          <summary className="tiny">Attributes ({structure.attributes.length})</summary>
          <Definitions items={structure.attributes} />
        </details>
      ) : null}
    </section>
  );
}
