/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent, act, waitFor } from "@testing-library/react";
import TeamListTab from "../TeamListTab";
import AddTeamsFMSReport from "../AddTeamsFMSReport";
import AddRemoveSingleTeam from "../AddRemoveSingleTeam";
import AddMultipleTeams from "../AddMultipleTeams";
import AttendingTeamList from "../AttendingTeamList";

// Mock child components to simplify testing
jest.mock("../AddTeamsFMSReport", () => ({
  __esModule: true,
  default: jest.fn(() => <div>Import FMS Report</div>),
}));

jest.mock("../AddRemoveSingleTeam", () => ({
  __esModule: true,
  default: jest.fn(() => <div>Add/Remove Single Team</div>),
}));

jest.mock("../AddMultipleTeams", () => ({
  __esModule: true,
  default: jest.fn(() => <div>Add Multiple Teams</div>),
}));

jest.mock("../AttendingTeamList", () => ({
  __esModule: true,
  default: jest.fn(() => <div>Currently Attending Teams</div>),
}));

describe("TeamListTab", () => {
  const mockMakeTrustedRequest = jest.fn();
  const mockMakeApiV3Request = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the main container with correct structure", () => {
    render(
      <TeamListTab
        selectedEvent="2025myevent"
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    expect(screen.getByText("Team List")).toBeInTheDocument();
    
    // Child components render their labels/content
    expect(screen.getByText("Import FMS Report")).toBeInTheDocument();
    expect(screen.getByText("Add/Remove Single Team")).toBeInTheDocument();
    expect(screen.getByText("Add Multiple Teams")).toBeInTheDocument();
    expect(screen.getByText("Currently Attending Teams")).toBeInTheDocument();
  });

  it("renders child components when an event is selected", () => {
    render(
      <TeamListTab
        selectedEvent="2025myevent"
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    // All child component sections should be visible
    expect(screen.getByText("Import FMS Report")).toBeInTheDocument();
    expect(screen.getByText("Add/Remove Single Team")).toBeInTheDocument();
    expect(screen.getByText("Add Multiple Teams")).toBeInTheDocument();
    expect(screen.getByText("Currently Attending Teams")).toBeInTheDocument();
  });

  it("renders when no event is selected", () => {
    render(
      <TeamListTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    expect(screen.getByText("Team List")).toBeInTheDocument();
  });
});

describe("TeamListTab callbacks shared with its children", () => {
  const mockMakeTrustedRequest = jest.fn();
  const mockMakeApiV3Request = jest.fn();
  const teams = [
    { key: "frc254", team_number: 254, nickname: "The Cheesy Poofs" },
    { key: "frc1114", team_number: 1114, nickname: "Simbotics" },
  ];

  const lastProps = (component: unknown): any => {
    const mock = component as jest.Mock;
    return mock.mock.calls[mock.mock.calls.length - 1][0];
  };

  const renderTab = (selectedEvent: string | null = "2025myevent") =>
    render(
      <TeamListTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

  beforeEach(() => {
    jest.clearAllMocks();
    mockMakeTrustedRequest.mockResolvedValue({ ok: true } as Response);
  });

  describe("updateTeamList", () => {
    it("posts the team keys and calls back on success", async () => {
      renderTab();
      const onSuccess = jest.fn();
      const onError = jest.fn();

      await act(async () => {
        await lastProps(AddMultipleTeams).updateTeamList(
          ["frc254", "frc1114"],
          onSuccess,
          onError
        );
      });

      expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
        "/api/trusted/v1/event/2025myevent/team_list/update",
        JSON.stringify(["frc254", "frc1114"])
      );
      expect(onSuccess).toHaveBeenCalledTimes(1);
      expect(onError).not.toHaveBeenCalled();
    });

    it("reports request failures through the error callback", async () => {
      mockMakeTrustedRequest.mockRejectedValueOnce(new Error("boom"));
      renderTab();
      const onSuccess = jest.fn();
      const onError = jest.fn();

      await act(async () => {
        await lastProps(AddTeamsFMSReport).updateTeamList(["frc254"], onSuccess, onError);
      });

      expect(onSuccess).not.toHaveBeenCalled();
      expect(onError).toHaveBeenCalledWith("Error: boom");
    });

    it("does nothing without a selected event", async () => {
      renderTab(null);
      const onSuccess = jest.fn();
      const onError = jest.fn();

      await act(async () => {
        await lastProps(AddRemoveSingleTeam).updateTeamList(["frc254"], onSuccess, onError);
      });

      expect(mockMakeTrustedRequest).not.toHaveBeenCalled();
      expect(onSuccess).not.toHaveBeenCalled();
      expect(onError).not.toHaveBeenCalled();
    });
  });

  describe("error dialog", () => {
    it("shows the message from showErrorMessage and closes on Close", async () => {
      renderTab();

      act(() => {
        lastProps(AddMultipleTeams).showErrorMessage("Something went wrong");
      });

      expect(screen.getByText("Error!")).toBeInTheDocument();
      expect(screen.getByText("Something went wrong")).toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "Close" }));

      await waitFor(() => {
        expect(screen.queryByText("Something went wrong")).not.toBeInTheDocument();
      });
    });
  });

  describe("fetchTeams", () => {
    it("returns an empty list without a selected event", async () => {
      renderTab(null);

      await expect(lastProps(AttendingTeamList).fetchTeams()).resolves.toEqual([]);
      expect(mockMakeApiV3Request).not.toHaveBeenCalled();
    });

    it("surfaces a non-2xx response in the error dialog", async () => {
      mockMakeApiV3Request.mockResolvedValue({
        ok: false,
        statusText: "Not Found",
      } as Response);
      renderTab();

      let result: unknown;
      await act(async () => {
        result = await lastProps(AttendingTeamList).fetchTeams();
      });

      expect(result).toEqual([]);
      expect(mockMakeApiV3Request).toHaveBeenCalledWith(
        "/api/v3/event/2025myevent/teams/simple"
      );
      expect(screen.getByText("Error fetching teams: Not Found")).toBeInTheDocument();
    });

    it("returns the parsed team list on success", async () => {
      mockMakeApiV3Request.mockResolvedValue({
        ok: true,
        json: async () => teams,
      } as Response);
      renderTab();

      await expect(lastProps(AttendingTeamList).fetchTeams()).resolves.toEqual(teams);
    });
  });

  describe("team list state", () => {
    it("shares fetched teams with the children and clears them on request", () => {
      renderTab();
      expect(lastProps(AddRemoveSingleTeam)).toMatchObject({
        hasFetchedTeams: false,
        currentTeams: [],
      });

      act(() => {
        lastProps(AttendingTeamList).updateTeams(teams);
      });
      expect(lastProps(AddRemoveSingleTeam)).toMatchObject({
        hasFetchedTeams: true,
        currentTeams: teams,
      });
      expect(lastProps(AttendingTeamList)).toMatchObject({
        hasFetchedTeams: true,
        teams,
      });

      act(() => {
        lastProps(AddTeamsFMSReport).clearTeams();
      });
      expect(lastProps(AddRemoveSingleTeam)).toMatchObject({
        hasFetchedTeams: false,
        currentTeams: [],
      });
    });

    it("clears fetched teams when the selected event changes", () => {
      const { rerender } = renderTab();
      act(() => {
        lastProps(AttendingTeamList).updateTeams(teams);
      });
      expect(lastProps(AttendingTeamList).hasFetchedTeams).toBe(true);

      rerender(
        <TeamListTab
          selectedEvent="2025other"
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      expect(lastProps(AttendingTeamList)).toMatchObject({
        hasFetchedTeams: false,
        teams: [],
      });
    });
  });
});
