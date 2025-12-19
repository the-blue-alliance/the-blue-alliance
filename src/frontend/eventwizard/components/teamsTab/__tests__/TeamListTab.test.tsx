/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import TeamListTab from "../TeamListTab";

// Mock child components to simplify testing
jest.mock("../AddTeamsFMSReport", () => ({
  __esModule: true,
  default: () => <div>Import FMS Report</div>,
}));

jest.mock("../AddRemoveSingleTeam", () => ({
  __esModule: true,
  default: () => <div>Add/Remove Single Team</div>,
}));

jest.mock("../AddMultipleTeams", () => ({
  __esModule: true,
  default: () => <div>Add Multiple Teams</div>,
}));

jest.mock("../AttendingTeamList", () => ({
  __esModule: true,
  default: () => <div>Currently Attending Teams</div>,
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
