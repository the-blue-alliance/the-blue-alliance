/* @jest-environment jsdom */

// Mock EnsureRequestSuccess to throw on non-ok responses
jest.mock("../../../net/EnsureRequestSuccess", () => (response) => {
  if (!response.ok) {
    throw new Error(response.statusText || "Request failed");
  }
  return response;
});

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AttendingTeamList from "../AttendingTeamList";

describe("AttendingTeamList", () => {
  beforeEach(() => {
    // default mock for fetch; individual tests will override as needed
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
    delete global.fetch;
  });

  test("renders 'No teams found' when fetched and teams empty", () => {
    const updateTeams = jest.fn();
    const showErrorMessage = jest.fn();

    render(
      <AttendingTeamList
        selectedEvent={"event1"}
        hasFetchedTeams={true}
        teams={[]}
        updateTeams={updateTeams}
        showErrorMessage={showErrorMessage}
      />
    );

    expect(screen.getByText(/No teams found/i)).toBeInTheDocument();
  });

  test("fetches teams and calls updateTeams on success and sets success class", async () => {
    const updateTeams = jest.fn();
    const showErrorMessage = jest.fn();

    const unsorted = [
      { team_number: 1114, key: "frc1114", nickname: "B" },
      { team_number: 254, key: "frc254", nickname: "A" },
    ];

    // Mock fetch to return ok response with json()
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(unsorted),
    });

    render(
      <AttendingTeamList
        selectedEvent={"2020test"}
        hasFetchedTeams={false}
        teams={[]}
        updateTeams={updateTeams}
        showErrorMessage={showErrorMessage}
      />
    );

    const button = screen.getByText(/Fetch Teams/i);
    expect(button).toBeEnabled();

    fireEvent.click(button);

    // updateTeams should be called with the sorted data
    await waitFor(() => expect(updateTeams).toHaveBeenCalledTimes(1));
    const calledWith = updateTeams.mock.calls[0][0];
    expect(calledWith[0].team_number).toBe(254);
    expect(calledWith[1].team_number).toBe(1114);

    // After success, button should contain success class
    expect(button.className).toContain("btn-success");
  });

  test("shows error and sets danger class when fetch fails", async () => {
    const updateTeams = jest.fn();
    const showErrorMessage = jest.fn();

    // Mock fetch to return a non-ok response
    global.fetch.mockResolvedValue({ ok: false, statusText: "Not Found" });

    render(
      <AttendingTeamList
        selectedEvent={"2020test"}
        hasFetchedTeams={false}
        teams={[]}
        updateTeams={updateTeams}
        showErrorMessage={showErrorMessage}
      />
    );

    const button = screen.getByText(/Fetch Teams/i);
    fireEvent.click(button);

    await waitFor(() => expect(showErrorMessage).toHaveBeenCalled());
    expect(showErrorMessage.mock.calls[0][0]).toMatch(/Not Found/i);
    expect(button.className).toContain("btn-danger");
  });

  test("disables Fetch Teams button when no selectedEvent", () => {
    const updateTeams = jest.fn();
    const showErrorMessage = jest.fn();

    render(
      <AttendingTeamList
        selectedEvent={null}
        hasFetchedTeams={false}
        teams={[]}
        updateTeams={updateTeams}
        showErrorMessage={showErrorMessage}
      />
    );

    const button = screen.getByText(/Fetch Teams/i);
    expect(button).toBeDisabled();
  });
});
