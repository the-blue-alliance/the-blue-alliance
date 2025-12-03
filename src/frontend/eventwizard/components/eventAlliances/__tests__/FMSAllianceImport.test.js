/**
 * @jest-environment jsdom
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import FMSAllianceImport from "../FMSAllianceImport";
import * as fmsAlliancesParser from "../../../utils/fmsAlliancesParser";

jest.mock("../../../utils/fmsAlliancesParser");

describe("FMSAllianceImport", () => {
  const mockUpdateAlliances = jest.fn();
  const mockSelectedEvent = "2025nysu";

  const getFileInput = (container) =>
    container.querySelector('input[type="file"]');

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders the import section", () => {
      const { container } = render(
        <FMSAllianceImport
          selectedEvent={mockSelectedEvent}
          updateAlliances={mockUpdateAlliances}
        />
      );

      expect(
        screen.getByText("Import FMS Alliance Report")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Upload the FMS Rankings Report/)
      ).toBeInTheDocument();
    });

    it("disables file input when no event is selected", () => {
      const { container } = render(
        <FMSAllianceImport
          selectedEvent=""
          updateAlliances={mockUpdateAlliances}
        />
      );

      const fileInput = container.querySelector('input[type="file"]');
      expect(fileInput).toBeDisabled();
    });

    it("enables file input when event is selected", () => {
      const { container } = render(
        <FMSAllianceImport
          selectedEvent={mockSelectedEvent}
          updateAlliances={mockUpdateAlliances}
        />
      );

      const fileInput = container.querySelector('input[type="file"]');
      expect(fileInput).not.toBeDisabled();
    });
  });

  describe("File Upload and Parsing", () => {
    it("parses file and displays confirmation dialog", async () => {
      const mockAlliances = [
        ["frc254", "frc971", "frc1323"],
        ["frc1678", "frc118", "frc2056"],
        ["frc973", "frc4414", "frc6418"],
      ];

      fmsAlliancesParser.parseFmsAlliancesFile.mockResolvedValue({
        alliances: mockAlliances,
        allianceCount: 3,
      });

      const { container } = render(
        <FMSAllianceImport
          selectedEvent={mockSelectedEvent}
          updateAlliances={mockUpdateAlliances}
        />
      );

      const fileInput = getFileInput(container);
      const file = new File([""], "test.xlsx", {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText(/Confirm Alliances:/)).toBeInTheDocument();
        expect(screen.getByText("254")).toBeInTheDocument();
        expect(screen.getByText("971")).toBeInTheDocument();
        expect(screen.getByText("1323")).toBeInTheDocument();
      });
    });

    it("displays error message on parse failure", async () => {
      fmsAlliancesParser.parseFmsAlliancesFile.mockRejectedValue(
        new Error("Invalid file format")
      );

      const { container } = render(
        <FMSAllianceImport
          selectedEvent={mockSelectedEvent}
          updateAlliances={mockUpdateAlliances}
        />
      );

      const fileInput = getFileInput(container);
      const file = new File([""], "test.xlsx");

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(
          screen.getByText("Error parsing file: Invalid file format")
        ).toBeInTheDocument();
      });
    });

    it("displays processing message while parsing", async () => {
      fmsAlliancesParser.parseFmsAlliancesFile.mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(
              () =>
                resolve({
                  alliances: [["frc254", "frc971", "frc1323"]],
                  allianceCount: 1,
                }),
              50
            );
          })
      );

      const { container } = render(
        <FMSAllianceImport
          selectedEvent={mockSelectedEvent}
          updateAlliances={mockUpdateAlliances}
        />
      );

      const fileInput = getFileInput(container);
      const file = new File([""], "test.xlsx");

      fireEvent.change(fileInput, { target: { files: [file] } });

      expect(screen.getByText("Processing file...")).toBeInTheDocument();

      await waitFor(() => {
        expect(screen.getByText(/Confirm Alliances:/)).toBeInTheDocument();
      });
    });

    it("handles alliances with 4 teams in confirmation dialog", async () => {
      const mockAlliances = [["frc254", "frc971", "frc1323", "frc1678"]];

      fmsAlliancesParser.parseFmsAlliancesFile.mockResolvedValue({
        alliances: mockAlliances,
        allianceCount: 1,
      });

      const { container } = render(
        <FMSAllianceImport
          selectedEvent={mockSelectedEvent}
          updateAlliances={mockUpdateAlliances}
        />
      );

      const fileInput = getFileInput(container);
      const file = new File([""], "test.xlsx");

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText("1678")).toBeInTheDocument();
      });
    });

    it("displays dashes for empty alliance positions", async () => {
      const mockAlliances = [["frc254"]];

      fmsAlliancesParser.parseFmsAlliancesFile.mockResolvedValue({
        alliances: mockAlliances,
        allianceCount: 1,
      });

      const { container } = render(
        <FMSAllianceImport
          selectedEvent={mockSelectedEvent}
          updateAlliances={mockUpdateAlliances}
        />
      );

      const fileInput = getFileInput(container);
      const file = new File([""], "test.xlsx");

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        const dashes = screen.getAllByText("-");
        // Should have dashes for Pick 1, Pick 2, and Pick 3
        expect(dashes.length).toBeGreaterThanOrEqual(3);
      });
    });
  });

  describe("Confirmation Dialog", () => {
    let container;

    beforeEach(async () => {
      const mockAlliances = [
        ["frc254", "frc971", "frc1323"],
        ["frc1678", "frc118", "frc2056"],
      ];

      fmsAlliancesParser.parseFmsAlliancesFile.mockResolvedValue({
        alliances: mockAlliances,
        allianceCount: 2,
      });

      const rendered = render(
        <FMSAllianceImport
          selectedEvent={mockSelectedEvent}
          updateAlliances={mockUpdateAlliances}
        />
      );
      container = rendered.container;

      const fileInput = getFileInput(container);
      const file = new File([""], "test.xlsx");

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(screen.getByText(/Confirm Alliances:/)).toBeInTheDocument();
      });
    });

    it("calls updateAlliances when Ok is clicked", async () => {
      mockUpdateAlliances.mockImplementation(
        (alliances, onSuccess, onError) => {
          onSuccess();
        }
      );

      const okButton = screen.getByRole("button", { name: "Ok" });
      fireEvent.click(okButton);

      await waitFor(() => {
        expect(mockUpdateAlliances).toHaveBeenCalledWith(
          [
            ["frc254", "frc971", "frc1323"],
            ["frc1678", "frc118", "frc2056"],
          ],
          expect.any(Function),
          expect.any(Function)
        );
      });
    });

    it("closes dialog and shows success message after upload", async () => {
      mockUpdateAlliances.mockImplementation(
        (alliances, onSuccess, onError) => {
          onSuccess();
        }
      );

      const okButton = screen.getByRole("button", { name: "Ok" });
      fireEvent.click(okButton);

      await waitFor(() => {
        expect(
          screen.queryByText(/Confirm Alliances:/)
        ).not.toBeInTheDocument();
        expect(
          screen.getByText("2 alliances uploaded to 2025nysu")
        ).toBeInTheDocument();
      });
    });

    it("closes dialog and shows error message on upload failure", async () => {
      mockUpdateAlliances.mockImplementation(
        (alliances, onSuccess, onError) => {
          onError("Network error");
        }
      );

      const okButton = screen.getByRole("button", { name: "Ok" });
      fireEvent.click(okButton);

      await waitFor(() => {
        expect(
          screen.queryByText(/Confirm Alliances:/)
        ).not.toBeInTheDocument();
        expect(screen.getByText("Error: Network error")).toBeInTheDocument();
      });
    });

    it("closes dialog without uploading when Cancel is clicked", async () => {
      const cancelButton = screen.getByRole("button", { name: "Cancel" });
      fireEvent.click(cancelButton);

      await waitFor(() => {
        expect(
          screen.queryByText(/Confirm Alliances:/)
        ).not.toBeInTheDocument();
      });

      expect(mockUpdateAlliances).not.toHaveBeenCalled();
    });
  });

  describe("Error Handling", () => {
    it("displays message when no alliances found in file", async () => {
      fmsAlliancesParser.parseFmsAlliancesFile.mockResolvedValue({
        alliances: [],
        allianceCount: 0,
      });

      const { container } = render(
        <FMSAllianceImport
          selectedEvent={mockSelectedEvent}
          updateAlliances={mockUpdateAlliances}
        />
      );

      const fileInput = getFileInput(container);
      const file = new File([""], "test.xlsx");

      fireEvent.change(fileInput, { target: { files: [file] } });

      await waitFor(() => {
        expect(
          screen.getByText(/No alliances found in the file/)
        ).toBeInTheDocument();
      });
    });
  });
});
