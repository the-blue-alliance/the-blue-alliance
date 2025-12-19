/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AddTeamsFMSReport from "../AddTeamsFMSReport";
import fs from "fs";
import path from "path";

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
