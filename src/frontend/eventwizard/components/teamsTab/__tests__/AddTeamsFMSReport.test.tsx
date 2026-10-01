/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AddTeamsFMSReport from "../AddTeamsFMSReport";
import fs from "fs";
import path from "path";
import XLSX from "xlsx";

describe("AddTeamsFMSReport", () => {
  const mockUpdateTeamList = jest.fn();
  const mockClearTeams = jest.fn();
  const mockShowErrorMessage = jest.fn();
  const mockMakeTrustedRequest = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("parses an FMS report and shows confirm dialog with 49 teams", async () => {
    // Load the real XLSX fixture from disk
    const fixturePath = path.join(
      __dirname,
      "data/2025nysu_TeamListReport.xlsx"
    );
    const fileData = fs.readFileSync(fixturePath);

    render(
      <AddTeamsFMSReport
        selectedEvent="2025nysu"
        updateTeamList={mockUpdateTeamList}
        clearTeams={mockClearTeams}
        showErrorMessage={mockShowErrorMessage}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    // Get the file input by querying DOM
    const actualFileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(actualFileInput).toBeInTheDocument();

    // Create a File object from the buffer
    const file = new File([fileData], "2025nysu_TeamListReport.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    // Simulate file selection
    fireEvent.change(actualFileInput, { target: { files: [file] } });

    // Wait for the dialog to appear with team count
    await waitFor(() => {
      expect(
        screen.getByText(/49 teams attending/i)
      ).toBeInTheDocument();
    });

    // Verify the dialog shows team list with first and last teams
    expect(screen.getByText(/Team 263/i)).toBeInTheDocument();
    expect(screen.getByText(/Team 10262/i)).toBeInTheDocument();
  });

  it("calls updateTeamList when confirm button is clicked", async () => {
    mockUpdateTeamList.mockImplementation(
      (teamKeys, onSuccess) => {
        onSuccess();
      }
    );

    const fixturePath = path.join(
      __dirname,
      "data/2025nysu_TeamListReport.xlsx"
    );
    const fileData = fs.readFileSync(fixturePath);

    render(
      <AddTeamsFMSReport
        selectedEvent="2025nysu"
        updateTeamList={mockUpdateTeamList}
        clearTeams={mockClearTeams}
        showErrorMessage={mockShowErrorMessage}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File([fileData], "2025nysu_TeamListReport.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    fireEvent.change(fileInput, { target: { files: [file] } });

    // Wait for the dialog and click confirm
    await waitFor(() => {
      expect(screen.getByText(/49 teams attending/i)).toBeInTheDocument();
    });

    const confirmButton = screen.getByRole("button", { name: /Ok/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockUpdateTeamList).toHaveBeenCalled();
      const teamKeys = mockUpdateTeamList.mock.calls[0][0];
      expect(teamKeys).toHaveLength(49);
      expect(teamKeys[0]).toBe("frc263");
      expect(teamKeys[teamKeys.length - 1]).toBe("frc10262");
    });
  });

  it("renders file input and import label", () => {
    render(
      <AddTeamsFMSReport
        selectedEvent="2025nysu"
        updateTeamList={mockUpdateTeamList}
        showErrorMessage={mockShowErrorMessage}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    expect(screen.getByText(/Import FMS Report/i)).toBeInTheDocument();
    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
  });
});

describe("AddTeamsFMSReport report validation and dialog actions", () => {
  const mockUpdateTeamList = jest.fn();
  const mockClearTeams = jest.fn();
  const mockShowErrorMessage = jest.fn();
  const mockMakeTrustedRequest = jest.fn();

  // Builds an FMS-style team list workbook: three title rows, then the header
  // row that the parser expects at row index 3.
  const makeReportFile = (rows: Array<Array<string | number>>): File => {
    const sheet = XLSX.utils.aoa_to_sheet([
      ["Team List Report"],
      [],
      [],
      ["#", "Short Name"],
      ...rows,
    ]);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, sheet, "Sheet1");
    const binary: string = XLSX.write(workbook, {
      type: "binary",
      bookType: "xlsx",
    });
    return new File([Buffer.from(binary, "binary")], "generated.xlsx");
  };

  const renderComponent = () =>
    render(
      <AddTeamsFMSReport
        selectedEvent="2025nysu"
        updateTeamList={mockUpdateTeamList}
        clearTeams={mockClearTeams}
        showErrorMessage={mockShowErrorMessage}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

  const fileInput = () =>
    document.querySelector('input[type="file"]') as HTMLInputElement;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("skips rows without a team number and rejects invalid ones", async () => {
    renderComponent();

    fireEvent.change(fileInput(), {
      target: { files: [makeReportFile([["", "Blank"], ["abc", "Bad"]])] },
    });

    await waitFor(() => {
      expect(mockShowErrorMessage).toHaveBeenCalledWith("Invalid team number NaN");
    });
    expect(screen.queryByText(/Confirm Teams/)).not.toBeInTheDocument();
  });

  it("explains when the report contains no team rows", async () => {
    renderComponent();

    fireEvent.change(fileInput(), { target: { files: [makeReportFile([])] } });

    expect(
      await screen.findByText(/No teams found in the file/)
    ).toBeInTheDocument();
    expect(screen.queryByText(/Confirm Teams/)).not.toBeInTheDocument();
  });

  it("clears the selection when the change event carries no file", () => {
    renderComponent();

    fireEvent.change(fileInput(), { target: { files: [] } });

    expect(screen.queryByText("Processing file...")).not.toBeInTheDocument();
    expect(screen.queryByText(/Confirm Teams/)).not.toBeInTheDocument();
  });

  it("closes the dialog without uploading when Cancel is clicked", async () => {
    renderComponent();
    fireEvent.change(fileInput(), {
      target: { files: [makeReportFile([[254, "The Cheesy Poofs"]])] },
    });
    await screen.findByText(/Confirm Teams: generated.xlsx/);

    fireEvent.click(screen.getByRole("button", { name: /Cancel/i }));

    await waitFor(() => {
      expect(screen.queryByText(/Confirm Teams/)).not.toBeInTheDocument();
    });
    expect(mockUpdateTeamList).not.toHaveBeenCalled();
  });

  it("reports upload failures through showErrorMessage", async () => {
    mockUpdateTeamList.mockImplementation((_keys, _onSuccess, onError) =>
      onError("Upload failed")
    );
    renderComponent();
    fireEvent.change(fileInput(), {
      target: { files: [makeReportFile([[254, "The Cheesy Poofs"]])] },
    });
    await screen.findByText(/Confirm Teams: generated.xlsx/);

    fireEvent.click(screen.getByRole("button", { name: /Ok/i }));

    expect(mockUpdateTeamList).toHaveBeenCalledWith(
      ["frc254"],
      expect.any(Function),
      expect.any(Function)
    );
    expect(mockShowErrorMessage).toHaveBeenCalledWith("Upload failed");
    expect(mockClearTeams).not.toHaveBeenCalled();
  });
});
