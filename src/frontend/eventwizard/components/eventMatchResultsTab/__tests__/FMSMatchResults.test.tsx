/**
 * @jest-environment jsdom
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import FMSMatchResults from "../FMSMatchResults";
import { parseResultsFile } from "../../../utils/resultsParser";
import fs from "fs";
import path from "path";
import {
  installMockFileReader,
  restoreFileReader,
} from "../../../utils/__tests__/testHelpers/mockFileReader";

jest.mock("../../../utils/resultsParser");

installMockFileReader();

// Mock crypto.subtle.digest for SHA-256 hashing
global.crypto.subtle = {
  digest: jest.fn(async (algorithm: string, data: ArrayBuffer) => {
    // Return a mock digest (in real tests, this would compute the actual SHA-256)
    // We'll just return a consistent buffer for testing
    const mockDigest = new ArrayBuffer(32);
    const view = new Uint8Array(mockDigest);
    view.fill(0xAB); // Fill with a constant value for predictable tests
    return mockDigest;
  }),
} as any;

describe("FMSMatchResults", () => {
  const mockMakeTrustedRequest = jest.fn();
  const selectedEvent = "2024nytr";

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders the component with correct headings and labels", () => {
      render(
        <FMSMatchResults
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(screen.getByText("FMS Match Results Import")).toBeInTheDocument();
      expect(
        screen.getByText(/Upload a FMS Match Results report/)
      ).toBeInTheDocument();
      expect(
        screen.getByLabelText("FMS Results Excel File")
      ).toBeInTheDocument();
    });

    it("renders playoff format options", () => {
      render(
        <FMSMatchResults
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(screen.getByText("Standard Bracket")).toBeInTheDocument();
      expect(screen.getByText("Double Elimination")).toBeInTheDocument();
    });

    it("renders alliance count options", () => {
      render(
        <FMSMatchResults
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(screen.getByText("8 Alliances")).toBeInTheDocument();
      expect(screen.getByText("16 Alliances")).toBeInTheDocument();
    });

    it("does not show confirmation dialog initially", () => {
      render(
        <FMSMatchResults
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      expect(
        screen.queryByText("Confirm Match Results Upload")
      ).not.toBeInTheDocument();
    });
  });

  describe("File Upload", () => {
    it("parses file and shows confirmation dialog on successful upload", async () => {
      const mockMatches = [
        {
          comp_level: "qm",
          set_number: 1,
          match_number: 1,
          alliances: {
            red: { teams: ["frc254", "frc971", "frc1678"], score: 100 },
            blue: { teams: ["frc1323", "frc2056", "frc5499"], score: 90 },
          },
          time_string: "9:00 AM",
          description: "Qual 1",
          tbaMatchKey: "2024nytr_qm1",
          timeString: "9:00 AM",
          rawRedTeams: ["254", "971", "1678"],
          rawBlueTeams: ["1323", "2056", "5499"],
        },
      ];

      (parseResultsFile as jest.Mock).mockResolvedValue(mockMatches);

      render(
        <FMSMatchResults
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const fileInput = screen.getByLabelText("FMS Results Excel File");
      const file = new File(["dummy content"], "test.xlsx", {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(parseResultsFile).toHaveBeenCalledWith(
          file,
          selectedEvent,
          false,
          false
        );
      });

      await waitFor(() => {
        expect(
          screen.getByText("Confirm Match Results Upload")
        ).toBeInTheDocument();
        expect(
          screen.getByText(/This will update 1 match on TBA/)
        ).toBeInTheDocument();
      });
    });

    it("shows error message on parse failure", async () => {
      (parseResultsFile as jest.Mock).mockRejectedValue(
        new Error("Parse failed")
      );

      render(
        <FMSMatchResults
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const fileInput = screen.getByLabelText("FMS Results Excel File");
      const file = new File(["dummy content"], "test.xlsx", {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(
          screen.getByText("Error parsing file: Parse failed")
        ).toBeInTheDocument();
      });
    });
  });

  describe("Confirmation Dialog", () => {
    beforeEach(async () => {
      const mockMatches = [
        {
          comp_level: "qm",
          set_number: 1,
          match_number: 1,
          alliances: {
            red: { teams: ["frc254", "frc971", "frc1678"], score: 100 },
            blue: { teams: ["frc1323", "frc2056", "frc5499"], score: 90 },
          },
          time_string: "9:00 AM",
          description: "Qual 1",
          tbaMatchKey: "2024nytr_qm1",
          timeString: "9:00 AM",
          rawRedTeams: ["254", "971", "1678"],
          rawBlueTeams: ["1323", "2056", "5499"],
        },
      ];

      (parseResultsFile as jest.Mock).mockResolvedValue(mockMatches);
    });

    it("uploads matches when confirmed", async () => {
      mockMakeTrustedRequest.mockResolvedValue({} as Response);

      render(
        <FMSMatchResults
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const fileInput = screen.getByLabelText("FMS Results Excel File");
      const file = new File(["dummy content"], "test.xlsx", {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });

      // Mock the arrayBuffer method on the file
      const arrayBuffer = new ArrayBuffer(12);
      const view = new Uint8Array(arrayBuffer);
      view.set([100, 117, 109, 109, 121, 32, 99, 111, 110, 116, 101, 110]);
      Object.defineProperty(file, "arrayBuffer", {
        value: jest.fn().mockResolvedValue(arrayBuffer),
      });

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(
          screen.getByText("Confirm Match Results Upload")
        ).toBeInTheDocument();
      });

      const confirmButton = screen.getByText("Confirm and Upload to TBA");
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
          `/api/trusted/v1/event/${selectedEvent}/matches/update`,
          expect.any(String)
        );
      });

      await waitFor(() => {
        expect(
          screen.getByText("Successfully uploaded 1 matches!")
        ).toBeInTheDocument();
      });
    });

    it("cancels upload when cancelled", async () => {
      render(
        <FMSMatchResults
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
        />
      );

      const fileInput = screen.getByLabelText("FMS Results Excel File");
      const file = new File(["dummy content"], "test.xlsx", {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });

      // Mock the arrayBuffer method on the file
      const arrayBuffer = new ArrayBuffer(12);
      const view = new Uint8Array(arrayBuffer);
      view.set([100, 117, 109, 109, 121, 32, 99, 111, 110, 116, 101, 110]);
      Object.defineProperty(file, "arrayBuffer", {
        value: jest.fn().mockResolvedValue(arrayBuffer),
      });

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(
          screen.getByText("Confirm Match Results Upload")
        ).toBeInTheDocument();
      });

      const cancelButton = screen.getByText("Cancel");
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(
          screen.queryByText("Confirm Match Results Upload")
        ).not.toBeInTheDocument();
        expect(screen.getByText("Upload cancelled")).toBeInTheDocument();
      });

      expect(mockMakeTrustedRequest).not.toHaveBeenCalled();
    });
  });
});

describe("FMSMatchResults re-parsing and upload edge cases", () => {
  const mockParseResultsFile = parseResultsFile as jest.Mock;
  const mockMakeTrustedRequest = jest.fn();
  const selectedEvent = "2024nytr";
  const file = new File(["dummy content"], "results.xlsx");
  // jsdom's File has no arrayBuffer(), which the report archival digest needs.
  Object.defineProperty(file, "arrayBuffer", {
    value: async () => new ArrayBuffer(8),
  });

  const makeMatch = (overrides: Record<string, unknown> = {}) => ({
    comp_level: "qm",
    set_number: 1,
    match_number: 1,
    alliances: {
      red: { teams: ["frc254", "frc971", "frc1678"], score: 100 },
      blue: { teams: ["frc1323", "frc2056", "frc5499"], score: 90 },
    },
    time_string: "9:00 AM",
    description: "Qualification 1",
    tbaMatchKey: "2024nytr_qm1",
    timeString: "9:00 AM",
    rawRedTeams: ["254", "971", "1678"],
    rawBlueTeams: ["1323", "2056", "5499"],
    ...overrides,
  });

  const renderComponent = () =>
    render(
      <FMSMatchResults
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

  const fileInput = () => screen.getByLabelText("FMS Results Excel File");

  const loadFile = async (): Promise<void> => {
    fireEvent.change(fileInput(), { target: { files: [file] } });
    await screen.findByText("Loaded 1 matches");
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockParseResultsFile.mockResolvedValue([makeMatch()]);
    mockMakeTrustedRequest.mockResolvedValue({ ok: true } as Response);
  });

  it("ignores a change event that carries no file", () => {
    renderComponent();

    fireEvent.change(fileInput(), { target: { files: [] } });

    expect(mockParseResultsFile).not.toHaveBeenCalled();
    expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
  });

  it("reports when the file contains no matches", async () => {
    mockParseResultsFile.mockResolvedValue([]);
    renderComponent();

    fireEvent.change(fileInput(), { target: { files: [file] } });

    expect(
      await screen.findByText("No matches found in the file.")
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Confirm Match Results Upload")
    ).not.toBeInTheDocument();
  });

  describe("re-parsing when settings change", () => {
    const triggers: Array<{
      name: string;
      prepare?: () => Promise<void>;
      trigger: () => void;
      expectedArgs: [boolean, boolean];
    }> = [
      {
        name: "alliance count",
        trigger: () => fireEvent.click(screen.getByLabelText("16 Alliances")),
        expectedArgs: [true, false],
      },
      {
        name: "double elimination playoff format",
        trigger: () =>
          fireEvent.click(screen.getByLabelText("Double Elimination")),
        expectedArgs: [false, true],
      },
      {
        name: "standard bracket playoff format",
        prepare: async () => {
          fireEvent.click(screen.getByLabelText("Double Elimination"));
          await waitFor(() => {
            expect(mockParseResultsFile).toHaveBeenCalledTimes(2);
          });
        },
        trigger: () => fireEvent.click(screen.getByLabelText("Standard Bracket")),
        expectedArgs: [false, false],
      },
    ];

    it("does not re-parse before a file has been chosen", () => {
      renderComponent();

      fireEvent.click(screen.getByLabelText("16 Alliances"));
      fireEvent.click(screen.getByLabelText("Double Elimination"));
      fireEvent.click(screen.getByLabelText("Standard Bracket"));

      expect(mockParseResultsFile).not.toHaveBeenCalled();
    });

    describe.each(triggers)("$name", ({ prepare, trigger, expectedArgs }) => {
      it("re-parses the loaded file with the new setting", async () => {
        renderComponent();
        await loadFile();
        if (prepare) await prepare();
        const match = makeMatch({ tbaMatchKey: "2024nytr_reparsed" });
        mockParseResultsFile.mockResolvedValueOnce([match, match]);

        trigger();

        expect(await screen.findByText("Loaded 2 matches")).toBeInTheDocument();
        expect(mockParseResultsFile).toHaveBeenLastCalledWith(
          file,
          selectedEvent,
          ...expectedArgs
        );
        expect(screen.getAllByText("2024nytr_reparsed")).toHaveLength(2);
        expect(screen.getByText("Confirm Match Results Upload")).toBeInTheDocument();
      });

      it("reports when the new setting yields no matches", async () => {
        renderComponent();
        await loadFile();
        if (prepare) await prepare();
        mockParseResultsFile.mockResolvedValueOnce([]);

        trigger();

        expect(
          await screen.findByText("No matches found in the file.")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("Confirm Match Results Upload")
        ).not.toBeInTheDocument();
      });

      it("surfaces parser errors from the re-parse", async () => {
        renderComponent();
        await loadFile();
        if (prepare) await prepare();
        mockParseResultsFile.mockRejectedValueOnce(new Error("re-parse failed"));

        trigger();

        expect(
          await screen.findByText("Error parsing file: re-parse failed")
        ).toBeInTheDocument();
        expect(
          screen.queryByText("Confirm Match Results Upload")
        ).not.toBeInTheDocument();
      });
    });
  });

  describe("uploading", () => {
    it("archives the report as playoff results when any playoff match is present", async () => {
      mockParseResultsFile.mockResolvedValue([
        makeMatch(),
        makeMatch({
          comp_level: "sf",
          set_number: 2,
          tbaMatchKey: "2024nytr_sf2m1",
          description: "Playoff 2",
        }),
      ]);
      renderComponent();
      fireEvent.change(fileInput(), { target: { files: [file] } });
      await screen.findByText("Loaded 2 matches");

      fireEvent.click(
        screen.getByRole("button", { name: "Confirm and Upload to TBA" })
      );

      expect(
        await screen.findByText("Successfully uploaded 2 matches!")
      ).toBeInTheDocument();
      expect(mockMakeTrustedRequest).toHaveBeenCalledTimes(2);
      expect(mockMakeTrustedRequest.mock.calls[1][0]).toBe(
        "/api/_eventwizard/event/2024nytr/fms_reports/playoff_results"
      );
    });

    it("shows the upload error and leaves the parsed matches in place", async () => {
      mockMakeTrustedRequest.mockRejectedValueOnce(new Error("boom"));
      renderComponent();
      await loadFile();

      fireEvent.click(
        screen.getByRole("button", { name: "Confirm and Upload to TBA" })
      );

      expect(
        await screen.findByText("Error uploading matches: Error: boom")
      ).toBeInTheDocument();
      expect(mockMakeTrustedRequest).toHaveBeenCalledTimes(1);
      // A later settings change still re-parses the retained file.
      mockParseResultsFile.mockResolvedValueOnce([makeMatch()]);
      fireEvent.click(screen.getByLabelText("16 Alliances"));
      await waitFor(() => {
        expect(mockParseResultsFile).toHaveBeenLastCalledWith(
          file,
          selectedEvent,
          true,
          false
        );
      });
    });
  });
});
