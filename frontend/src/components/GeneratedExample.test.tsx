import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import GeneratedExampleBlock, { unlinkedObjectsText } from "./GeneratedExample";

afterEach(cleanup);

describe("GeneratedExampleBlock", () => {
  it("says which objects the generated example does not link to the asked one", () => {
    const example = {
      valid: true,
      attempts: 3,
      origin: "generated" as const,
      askedObject: "Line",
      xml: "<CompositeFrame/>",
      unlinkedObjects: [
        { element: "VehicleType", id: "hd:VT" },
        { element: "ScheduledStopPoint", id: "hd:S1" },
        { element: "ScheduledStopPoint", id: "hd:S2" },
      ],
    };
    render(<GeneratedExampleBlock example={example} />);
    expect(screen.getByText("In this example nothing links the VehicleType and 2 ScheduledStopPoints to the Line.")).toBeTruthy();
    expect(unlinkedObjectsText({ ...example, unlinkedObjects: [] })).toBe("");
    expect(unlinkedObjectsText({ ...example, unlinkedObjects: [{ element: "DayType", id: "d" }] })).toBe(
      "In this example nothing links the DayType to the Line.",
    );
  });

  it("labels a standard example shown instead of a generated one as not holding the asked values", () => {
    render(
      <GeneratedExampleBlock
        example={{
          valid: true,
          attempts: 0,
          origin: "standard",
          validated: true,
          holdsValues: false,
          missingValues: ["5", "EUR"],
          schemaVersion: "2.0",
          sourcePath: "examples/fares/Netex_61.2_AdultChildProduct.xml",
          sourceUrl: "https://github.com/x/NeTEx/blob/98365bd/examples/fares/Netex_61.2_AdultChildProduct.xml",
          xml: "<FareFrame/>",
          valuePlaces: [],
        }}
      />,
    );
    expect(screen.getByRole("heading").textContent).toContain(
      "Netex_61.2_AdultChildProduct.xml (does not contain the asked values 5, EUR)",
    );
    expect(screen.getByText(/No example with the asked values 5, EUR validated against the schema/)).toBeTruthy();
    expect(screen.queryByRole("list", { name: "Where the question's values go" })).toBeNull();
  });

  it("shows a valid fragment labelled as generated, with the schema version", () => {
    render(
      <GeneratedExampleBlock
        example={{
          valid: true,
          attempts: 1,
          xml: "<ResourceFrame>\n  <vehicleTypes/>\n</ResourceFrame>",
          document: "<PublicationDelivery/>",
          schemaVersion: "2.0",
          schemaCommit: "37ff1e453596",
        }}
      />,
    );
    expect(screen.getByRole("heading").textContent).toBe("Generated example for this question (valid against NeTEx 2.0, commit 37ff1e4)");
    expect(screen.getByText(/commit 37ff1e4/)).toBeTruthy();
    expect(screen.getByText(/<ResourceFrame>/)).toBeTruthy();
    // The block's one button is the download, next to the fragment; copying is the answer's Copy answer.
    expect(screen.getAllByRole("button").map((b) => b.getAttribute("aria-label"))).toEqual([
      "Download generated example as XML file",
    ]);
  });

  it("says where each value of the question goes, before the fragment", () => {
    render(
      <GeneratedExampleBlock
        example={{
          valid: true,
          attempts: 1,
          xml: "<ResourceFrame/>",
          valuePlaces: [
            { value: "49", element: "SeatingCapacity", path: ["ResourceFrame", "vehicleTypes", "VehicleType", "capacities", "PassengerCapacity"] },
            { value: "1", element: "WheelchairPlaceCapacity", path: ["ResourceFrame", "vehicleTypes", "VehicleType", "capacities", "PassengerCapacity"] },
          ],
        }}
      />,
    );
    const lead = screen.getByRole("list", { name: "Where the question's values go" });
    expect(lead.textContent).toContain("49 → SeatingCapacity in VehicleType › capacities › PassengerCapacity");
    expect(lead.textContent).toContain("1 → WheelchairPlaceCapacity");
  });

  it("names the standard's file for an example taken from the standard, with counts in the lead", () => {
    render(
      <GeneratedExampleBlock
        example={{
          valid: true,
          attempts: 0,
          origin: "standard",
          validated: false,
          schemaCommit: "98365bd4341d",
          sourcePath: "examples/standards/nta/AllStations.xml",
          sourceUrl: "https://github.com/x/NeTEx/blob/98365bd/examples/standards/nta/AllStations.xml",
          xml: "<SiteFrame/>",
          valuePlaces: [{ value: "two", element: "Quay", count: 2, path: ["SiteFrame", "stopPlaces", "StopPlace", "quays"] }],
        }}
      />,
    );
    expect(screen.getByRole("heading").textContent).toBe("Example from the standard: AllStations.xml (as published, commit 98365bd)");
    expect(screen.getByRole("link", { name: "AllStations.xml" }).getAttribute("href")).toContain("/blob/");
    expect(screen.getByRole("list", { name: "Where the question's values go" }).textContent).toContain("two → 2 × Quay in stopPlaces › StopPlace › quays");
  });

  it("labels an excerpt of a standard example and leads with the asked-for part", () => {
    render(
      <GeneratedExampleBlock
        example={{
          valid: true,
          attempts: 0,
          origin: "standard",
          validated: false,
          excerpt: true,
          schemaCommit: "98365bd4341d",
          sourcePath: "examples/functions/stopPlace/Wimbledon.xml",
          xml: "<SiteFrame/>",
          valuePlaces: [{ value: "an elevator", element: "LiftEquipment", path: ["StopPlace", "pathLinks", "SitePathLink", "placeEquipments"] }],
        }}
      />,
    );
    expect(screen.getByRole("heading").textContent).toBe("Example from the standard: Wimbledon.xml (excerpt as published, commit 98365bd)");
    expect(screen.getByRole("list", { name: "Where the question's values go" }).textContent).toContain(
      "an elevator → LiftEquipment in pathLinks › SitePathLink › placeEquipments",
    );
  });

  it("explains each element in the schema's words", () => {
    render(
      <GeneratedExampleBlock
        example={{
          valid: true,
          attempts: 1,
          xml: "<ResourceFrame/>",
          elementNotes: [
            { name: "SeatingCapacity", documentation: "The seating capacity of vehicles of the type." },
            { name: "StandingCapacity", documentation: "The standing capacity of vehicles of the type." },
          ],
        }}
      />,
    );
    expect(screen.getByText(/in the words of the NeTEx schema/)).toBeTruthy();
    expect(screen.getByText("SeatingCapacity")).toBeTruthy();
    expect(screen.getByText("The standing capacity of vehicles of the type.")).toBeTruthy();
  });

  it("shows no notes block without notes", () => {
    render(<GeneratedExampleBlock example={{ valid: true, attempts: 1, xml: "<ResourceFrame/>", elementNotes: [] }} />);
    expect(screen.queryByText(/in the words of the NeTEx schema/)).toBeNull();
  });

  it("never shows XML that did not validate", () => {
    render(<GeneratedExampleBlock example={{ valid: false, attempts: 3, errors: ["line 1: ..."] }} />);
    expect(screen.getByText(/No NeTEx example valid against the schema/)).toBeTruthy();
    expect(screen.queryByText(/^Generated example/)).toBeNull();
  });

  it("renders nothing when no example was asked for", () => {
    const { container } = render(<GeneratedExampleBlock example={null} />);
    expect(container.textContent).toBe("");
  });
});
