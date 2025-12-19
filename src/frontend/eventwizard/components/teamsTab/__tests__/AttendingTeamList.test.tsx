/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AttendingTeamList from "../AttendingTeamList";

describe("AttendingTeamList", () => {
  const mockUpdateTeams = jest.fn();
  const mockShowErrorMessage = jest.fn();
  const mockFetchTeams = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders 'No teams found' when fetched and teams empty", () => {
    render(
      <AttendingTeamList
        selectedEvent="event1"
        hasFetchedTeams={true}
        teams={[]}
        fetchTeams={mockFetchTeams}
        updateTeams={mockUpdateTeams}
        showErrorMessage={mockShowErrorMessage}
      />
    );

    expect(screen.getByText(/No teams found/i)).toBeInTheDocument();
  });

  test("fetches teams and calls updateTeams on success and sets success class", async () => {
    const unsorted = [
      { team_number: 1114, key: "frc1114", nickname: "B" },
      { team_number: 254, key: "frc254", nickname: "A" },
    ];

    mockFetchTeams.mockResolvedValue(unsorted);

    render(
      <AttendingTeamList
        selectedEvent="2020test"
        hasFetchedTeams={false}
        teams={[]}
        fetchTeams={mockFetchTeams}
        updateTeams={mockUpdateTeams}
        showErrorMessage={mockShowErrorMessage}
      />
    );

    const button = screen.getByText(/Fetch Teams/i);
    expect(button).toBeEnabled();

    fireEvent.click(button);

    // updateTeams should be called with the sorted data
    await waitFor(() => expect(mockUpdateTeams).toHaveBeenCalledTimes(1));
    const calledWith = mockUpdateTeams.mock.calls[0][0];
    expect(calledWith[0].team_number).toBe(254);
    expect(calledWith[1].team_number).toBe(1114);

    // After success, button should contain success class
    expect(button.className).toContain("btn-success");
  });

  test("shows error and sets danger class when fetch fails", async () => {
    mockFetchTeams.mockRejectedValue(new Error("Not Found"));

    render(
      <AttendingTeamList
        selectedEvent="2020test"
        hasFetchedTeams={false}
        teams={[]}
        fetchTeams={mockFetchTeams}
        updateTeams={mockUpdateTeams}
        showErrorMessage={mockShowErrorMessage}
      />
    );

    const button = screen.getByText(/Fetch Teams/i);
    fireEvent.click(button);

    await waitFor(() => expect(mockShowErrorMessage).toHaveBeenCalled());
    expect(mockShowErrorMessage.mock.calls[0][0]).toMatch(/Error: Not Found/i);
    expect(button.className).toContain("btn-danger");
  });

  test("disables Fetch Teams button when no selectedEvent", () => {
    render(
      <AttendingTeamList
        selectedEvent={null}
        hasFetchedTeams={false}
        teams={[]}
        fetchTeams={mockFetchTeams}
        updateTeams={mockUpdateTeams}
        showErrorMessage={mockShowErrorMessage}
      />
    );

    const button = screen.getByText(/Fetch Teams/i);
    expect(button).toBeDisabled();
  });

  test("displays team list when teams are present", () => {
    const teams = [
      { team_number: 254, key: "frc254", nickname: "The Cheesy Poofs" },
      { team_number: 1114, key: "frc1114", nickname: "Simbotics" },
    ];

    render(
      <AttendingTeamList
        selectedEvent="2020test"
        hasFetchedTeams={true}
        teams={teams}
        fetchTeams={mockFetchTeams}
        updateTeams={mockUpdateTeams}
        showErrorMessage={mockShowErrorMessage}
      />
    );

    expect(screen.getByText(/254/)).toBeInTheDocument();
    expect(screen.getByText(/1114/)).toBeInTheDocument();
  });
});
