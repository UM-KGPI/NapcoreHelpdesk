/**
 * Download a generated NeTEx example as the validated PublicationDelivery document: a complete XML file
 * ready for an editor or a validator, which copying the answer text cannot replace. Offered as an icon
 * button in the answer's action group.
 */
import type { GeneratedExample } from "../types";

export function downloadPublicationDelivery(example: GeneratedExample): void {
  const blob = new Blob([example.document ?? example.xml ?? ""], { type: "application/xml" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "netex-generated-example.xml";
  link.click();
  URL.revokeObjectURL(url);
}
