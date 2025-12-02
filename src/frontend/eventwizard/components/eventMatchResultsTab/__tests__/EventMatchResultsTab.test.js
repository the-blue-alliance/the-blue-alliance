import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import EventMatchResultsTab from "../EventMatchResultsTab";

describe("EventMatchResultsTab", () => {
  const mockMakeTrustedRequest = jest.fn();
  const selectedEvent = "2024nytr";

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders the main tab structure with correct headings and labels", () => {
      const html = renderToStaticMarkup(
        <EventMatchResultsTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain('id="results"');
      expect(html).toContain("Upload Match Results");
      expect(html).toContain("FMS Results Excel File");
      expect(html).toContain("Playoff Format");
      expect(html).toContain("Number of Playoff Alliances");
    });

    it("renders playoff format options", () => {
      const html = renderToStaticMarkup(
        <EventMatchResultsTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain('name="playoff-format-results"');
      expect(html).toContain('value="standard"');
      expect(html).toContain("Standard Bracket");
      expect(html).toContain('value="doubleelim"');
      expect(html).toContain("Double Elimination");
    });

    it("renders alliance count options", () => {
      const html = renderToStaticMarkup(
        <EventMatchResultsTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain('name="alliance-count-results"');
      expect(html).toContain('value="8"');
      expect(html).toContain("8 Alliances");
      expect(html).toContain('value="16"');
      expect(html).toContain("16 Alliances");
    });
  });

  describe("Component Structure", () => {
    it("contains file input for results upload", () => {
      const html = renderToStaticMarkup(
        <EventMatchResultsTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain('type="file"');
      expect(html).toContain('id="results_file"');
      expect(html).toContain('accept=".xls,.xlsx"');
    });

    it("contains radio buttons for playoff format", () => {
      const html = renderToStaticMarkup(
        <EventMatchResultsTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain('type="radio"');
      expect(html).toContain('name="playoff-format-results"');
    });

    it("does not show preview table initially", () => {
      const html = renderToStaticMarkup(
        <EventMatchResultsTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).not.toContain("Match Results Preview");
    });

    it("disables file input when no event is selected", () => {
      const html = renderToStaticMarkup(
        <EventMatchResultsTab
          selectedEvent={null}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain('disabled=""');
    });

    it("enables file input when event is selected", () => {
      const html = renderToStaticMarkup(
        <EventMatchResultsTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain('id="results_file"');
      // When enabled, should not have disabled attribute (or it should be false)
      const fileInputMatch = html.match(/<input[^>]*id="results_file"[^>]*>/);
      expect(fileInputMatch).toBeTruthy();
      // Check that disabled is not set or is set to false
      const hasDisabled =
        fileInputMatch[0].includes('disabled=""') ||
        fileInputMatch[0].includes('disabled="disabled"');
      expect(hasDisabled).toBe(false);
    });

    it("renders description about overwriting data", () => {
      const html = renderToStaticMarkup(
        <EventMatchResultsTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain("overwrite data");
    });
  });
});
