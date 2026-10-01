/* @jest-environment jsdom */
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventScheduleTab from "../EventScheduleTab";
import { parseScheduleFile, ScheduleMatch } from "../../../utils/scheduleParser";
import { uploadFmsReport } from "../../../utils/fmsReportUpload";

jest.mock("../../../utils/scheduleParser");
jest.mock("../../../utils/fmsReportUpload");

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

describe("EventScheduleTab interactions", () => {
  const mockParseScheduleFile = parseScheduleFile as jest.Mock;
  const mockUploadFmsReport = uploadFmsReport as jest.Mock;
  const mockMakeTrustedRequest = jest.fn();
  const selectedEvent = "2025nysu";
  const file = new File(["schedule"], "2025nysu_ScheduleReport_Quals.xlsx");

  const makeMatch = (overrides: Partial<ScheduleMatch> = {}): ScheduleMatch => ({
    comp_level: "qm",
    set_number: 1,
    match_number: 1,
    alliances: {
      red: { teams: ["frc0254", "frc1114", "frc2056"], score: null },
      blue: { teams: ["frc0000", "frc0033", "frc0067"], score: null },
    },
    time_string: "9:00 AM",
    tbaMatchKey: "2025nysu_qm1",
    timeString: "9:00 AM",
    description: "Qualification 1",
    rawMatchNumber: 1,
    ...overrides,
  });

  const renderTab = () =>
    render(
      <EventScheduleTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

  const fileInput = () =>
    screen.getByLabelText("FMS Schedule Excel File") as HTMLInputElement;

  const loadFile = async (): Promise<void> => {
    fireEvent.change(fileInput(), { target: { files: [file] } });
    await screen.findByText("Loaded 1 matches");
  };

  beforeEach(() => {
    mockParseScheduleFile.mockResolvedValue([makeMatch()]);
    mockUploadFmsReport.mockResolvedValue(undefined);
    mockMakeTrustedRequest.mockResolvedValue({ ok: true } as Response);
    window.alert = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
    jest.useRealTimers();
  });

  describe("File selection", () => {
    it("ignores a change event that carries no file", () => {
      renderTab();

      fireEvent.change(fileInput(), { target: { files: [] } });

      expect(mockParseScheduleFile).not.toHaveBeenCalled();
      expect(screen.queryByText(/Parsing schedule file/)).not.toBeInTheDocument();
    });

    it("parses the file with the current settings and previews the matches", async () => {
      renderTab();

      await loadFile();

      expect(mockParseScheduleFile).toHaveBeenCalledWith(
        file,
        selectedEvent,
        "all",
        false,
        false
      );
      expect(screen.getByText("Match Preview")).toBeInTheDocument();
      expect(screen.getByText("2025nysu_qm1")).toBeInTheDocument();
      expect(screen.getByText("Qualification 1")).toBeInTheDocument();
      // Leading zeros are stripped from team numbers, and "0000" becomes "0".
      const cells = screen.getAllByRole("cell").map((cell) => cell.textContent);
      expect(cells).toEqual([
        "9:00 AM",
        "Qualification 1",
        "1",
        "2025nysu_qm1",
        "0",
        "33",
        "67",
        "254",
        "1114",
        "2056",
      ]);
      expect(
        screen.getByRole("button", { name: "Upload Matches to TBA" })
      ).toBeInTheDocument();
    });

    it("reports when the file yields no matches for the current settings", async () => {
      mockParseScheduleFile.mockResolvedValue([]);
      renderTab();

      fireEvent.change(fileInput(), { target: { files: [file] } });

      expect(
        await screen.findByText("No matches found with current settings.")
      ).toBeInTheDocument();
      expect(screen.queryByText("Match Preview")).not.toBeInTheDocument();
    });

    it("surfaces parser errors and clears any previous preview", async () => {
      renderTab();
      await loadFile();
      mockParseScheduleFile.mockRejectedValueOnce(new Error("bad workbook"));

      fireEvent.change(fileInput(), { target: { files: [file] } });

      expect(
        await screen.findByText("Error parsing file: bad workbook")
      ).toBeInTheDocument();
      expect(screen.queryByText("Match Preview")).not.toBeInTheDocument();
    });
  });

  describe("Re-parsing when settings change", () => {
    const triggers: Array<{
      name: string;
      prepare?: () => Promise<void>;
      trigger: () => void;
      expectedArgs: [string, boolean, boolean];
    }> = [
      {
        name: "competition level filter",
        trigger: () => fireEvent.click(screen.getByLabelText("Qualifications")),
        expectedArgs: ["qm", false, false],
      },
      {
        name: "alliance count",
        trigger: () => fireEvent.click(screen.getByLabelText("16 Alliances")),
        expectedArgs: ["all", true, false],
      },
      {
        name: "double elimination playoff format",
        trigger: () =>
          fireEvent.click(screen.getByLabelText("Double Elimination")),
        expectedArgs: ["all", false, true],
      },
      {
        name: "standard bracket playoff format",
        prepare: async () => {
          fireEvent.click(screen.getByLabelText("Double Elimination"));
          await waitFor(() => {
            expect(mockParseScheduleFile).toHaveBeenCalledTimes(2);
          });
        },
        trigger: () => fireEvent.click(screen.getByLabelText("Standard Bracket")),
        expectedArgs: ["all", false, false],
      },
    ];

    it("does not re-parse before a file has been chosen", () => {
      renderTab();

      fireEvent.click(screen.getByLabelText("Qualifications"));
      fireEvent.click(screen.getByLabelText("16 Alliances"));
      fireEvent.click(screen.getByLabelText("Double Elimination"));
      fireEvent.click(screen.getByLabelText("Standard Bracket"));

      expect(mockParseScheduleFile).not.toHaveBeenCalled();
      expect(screen.getByLabelText("Qualifications")).toBeChecked();
    });

    describe.each(triggers)("$name", ({ prepare, trigger, expectedArgs }) => {
      it("re-parses the loaded file with the new setting", async () => {
        renderTab();
        await loadFile();
        if (prepare) await prepare();
        const match = makeMatch({ tbaMatchKey: "2025nysu_reparsed" });
        mockParseScheduleFile.mockResolvedValueOnce([match, match]);

        trigger();

        expect(await screen.findByText("Loaded 2 matches")).toBeInTheDocument();
        expect(mockParseScheduleFile).toHaveBeenLastCalledWith(
          file,
          selectedEvent,
          ...expectedArgs
        );
        expect(screen.getAllByText("2025nysu_reparsed")).toHaveLength(2);
      });

      it("reports when the new setting matches nothing", async () => {
        renderTab();
        await loadFile();
        if (prepare) await prepare();
        mockParseScheduleFile.mockResolvedValueOnce([]);

        trigger();

        expect(
          await screen.findByText("No matches found with current settings.")
        ).toBeInTheDocument();
        expect(screen.queryByText("Match Preview")).not.toBeInTheDocument();
      });

      it("surfaces parser errors from the re-parse", async () => {
        renderTab();
        await loadFile();
        if (prepare) await prepare();
        mockParseScheduleFile.mockRejectedValueOnce(new Error("re-parse failed"));

        trigger();

        expect(
          await screen.findByText("Error parsing file: re-parse failed")
        ).toBeInTheDocument();
        expect(screen.queryByText("Match Preview")).not.toBeInTheDocument();
      });
    });
  });

  describe("Uploading", () => {
    it("posts the matches, archives the report and resets after three seconds", async () => {
      jest.useFakeTimers();
      renderTab();
      await loadFile();

      fireEvent.click(screen.getByRole("button", { name: "Upload Matches to TBA" }));

      expect(
        await screen.findByText("Successfully uploaded 1 matches to TBA!")
      ).toBeInTheDocument();
      expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
        "event/2025nysu/matches/update",
        JSON.stringify([
          {
            comp_level: "qm",
            set_number: 1,
            match_number: 1,
            alliances: makeMatch().alliances,
            time: "9:00 AM",
          },
        ])
      );
      expect(mockUploadFmsReport).toHaveBeenCalledWith(
        file,
        selectedEvent,
        "qual_schedule",
        mockMakeTrustedRequest
      );

      act(() => {
        jest.advanceTimersByTime(3000);
      });

      expect(
        screen.queryByText("Successfully uploaded 1 matches to TBA!")
      ).not.toBeInTheDocument();
      expect(screen.queryByText("Match Preview")).not.toBeInTheDocument();
      expect(fileInput().value).toBe("");
    });

    it("archives a playoff schedule when a playoff level filter is active", async () => {
      renderTab();
      fireEvent.click(screen.getByLabelText("Semifinals"));
      await loadFile();

      fireEvent.click(screen.getByRole("button", { name: "Upload Matches to TBA" }));

      await waitFor(() => {
        expect(mockUploadFmsReport).toHaveBeenCalledWith(
          file,
          selectedEvent,
          "playoff_schedule",
          mockMakeTrustedRequest
        );
      });
    });

    it("shows the upload error and keeps the preview", async () => {
      mockMakeTrustedRequest.mockRejectedValueOnce(new Error("boom"));
      renderTab();
      await loadFile();

      fireEvent.click(screen.getByRole("button", { name: "Upload Matches to TBA" }));

      expect(
        await screen.findByText("Error uploading matches: Error: boom")
      ).toBeInTheDocument();
      expect(mockUploadFmsReport).not.toHaveBeenCalled();
      expect(screen.getByText("Match Preview")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Upload Matches to TBA" })
      ).toBeEnabled();
    });
  });
});
