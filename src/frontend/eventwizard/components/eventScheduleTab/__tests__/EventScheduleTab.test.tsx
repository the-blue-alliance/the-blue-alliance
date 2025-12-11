import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import EventScheduleTab from "../EventScheduleTab";

describe("EventScheduleTab", () => {
  const mockMakeTrustedRequest = jest.fn();
  const mockSelectedEvent = "2025nysu";

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders the main tab structure with correct headings and labels", () => {
      const html = renderToStaticMarkup(
        <EventScheduleTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain("FMS Schedule Import");
      expect(html).toContain("Upload FMS Schedule Report");
      expect(html).toContain("FMS Schedule Excel File");
      expect(html).toContain("Competition Level Filter");
      expect(html).toContain("Playoff Format");
      expect(html).toContain("Number of Playoff Alliances");
    });

    it("renders all competition level options", () => {
      const html = renderToStaticMarkup(
        <EventScheduleTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain("Qualifications");
      expect(html).toContain("Octofinals");
      expect(html).toContain("Quarterfinals");
      expect(html).toContain("Semifinals");
      expect(html).toContain("Finals");
    });

    it("renders playoff format options", () => {
      const html = renderToStaticMarkup(
        <EventScheduleTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain("Standard Bracket");
      expect(html).toContain("Double Elimination");
    });

    it("renders alliance count options", () => {
      const html = renderToStaticMarkup(
        <EventScheduleTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain("8 Alliances");
      expect(html).toContain("16 Alliances");
    });
  });

  describe("Component Structure", () => {
    it("contains file input for schedule upload", () => {
      const html = renderToStaticMarkup(
        <EventScheduleTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain('type="file"');
      expect(html).toContain('accept=".xls,.xlsx"');
    });

    it("contains radio buttons for filters", () => {
      const html = renderToStaticMarkup(
        <EventScheduleTab
          selectedEvent={mockSelectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(html).toContain('type="radio"');
      expect(html).toContain('name="import-comp-level"');
      expect(html).toContain('name="playoff-format"');
      expect(html).toContain('name="alliance-count-schedule"');
    });
  });
});
