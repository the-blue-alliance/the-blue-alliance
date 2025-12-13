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
