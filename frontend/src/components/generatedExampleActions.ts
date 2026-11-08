/**
 * Actions on a generated NeTEx example, offered as icon buttons in the answer's action group (next to
 * copy answer, export, like, dislike): copy the fragment, download the validated PublicationDelivery.
 */
import type { GeneratedExample } from "../types";

export async function copyFragment(example: GeneratedExample): Promise<void> {
  const text = example.xml ?? "";
  if (!text) return;
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const temp = document.createElement("textarea");
  temp.value = text;
  temp.setAttribute("readonly", "true");
  temp.style.position = "absolute";
  temp.style.left = "-9999px";
  document.body.appendChild(temp);
  temp.select();
  document.execCommand("copy");
  document.body.removeChild(temp);
}

export function downloadPublicationDelivery(example: GeneratedExample): void {
  const blob = new Blob([example.document ?? example.xml ?? ""], { type: "application/xml" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "netex-generated-example.xml";
  link.click();
  URL.revokeObjectURL(url);
}
