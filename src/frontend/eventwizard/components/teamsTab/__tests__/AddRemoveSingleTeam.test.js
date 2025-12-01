/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import AddRemoveSingleTeam from "../AddRemoveSingleTeam";

describe("AddRemoveSingleTeam", () => {
  beforeEach(() => {
    // Mock fetch used in componentDidMount
    global.fetch = jest.fn().mockResolvedValue({
      json: jest.fn().mockResolvedValue([]),
    });
  });

  afterEach(() => {
    delete global.fetch;
  });
  test("selection updates selectedTeamKey on instance", () => {
    const updateTeamList = jest.fn();
    const showErrorMessage = jest.fn();

    const ref = React.createRef();
    render(
      <AddRemoveSingleTeam
        ref={ref}
        selectedEvent={"event1"}
        updateTeamList={updateTeamList}
        hasFetchedTeams={true}
        currentTeams={[]}
        showErrorMessage={showErrorMessage}
      />
    );

    // Simulate selecting a team from typeahead
    act(() => {
      ref.current.onTeamSelectionChanged(["254 | Example Team"]);
    });

    expect(ref.current.state.selectedTeamKey).toBe("frc254");
  });

  test("clicking Add Team calls updateTeamList and clearTeams on success", async () => {
    const updateTeamList = jest.fn();
    const clearTeams = jest.fn();
    const showErrorMessage = jest.fn();

    const ref = React.createRef();
    render(
      <AddRemoveSingleTeam
        ref={ref}
        selectedEvent={"event1"}
        updateTeamList={updateTeamList}
        hasFetchedTeams={true}
        currentTeams={[]}
        clearTeams={clearTeams}
        showErrorMessage={showErrorMessage}
      />
    );

    // select team
    act(() => {
      ref.current.onTeamSelectionChanged(["254 | Example Team"]);
    });

    const button = screen.getByText(/Add Team/i);
    expect(button).toBeEnabled();

    // Click the Add Team button which triggers updateTeamList
    fireEvent.click(button);

    expect(updateTeamList).toHaveBeenCalledTimes(1);
    const callArgs = updateTeamList.mock.calls[0];
    expect(callArgs[0]).toEqual(["frc254"]);

    // Provide a mock typeahead instance so success callback can call clear()
    ref.current.teamTypeahead = { getInstance: () => ({ clear: jest.fn() }) };

    const successCallback = callArgs[1];
    act(() => {
      successCallback();
    });

    await waitFor(() => expect(clearTeams).toHaveBeenCalledTimes(1));
    expect(button.className).toContain("btn-success");
  });

  test("clicking Remove Team calls updateTeamList and clearTeams on success", async () => {
    const updateTeamList = jest.fn();
    const clearTeams = jest.fn();
    const showErrorMessage = jest.fn();

    const ref = React.createRef();
    // currentTeams includes frc254 so removal is valid (supply full shape)
    render(
      <AddRemoveSingleTeam
        ref={ref}
        selectedEvent={"event1"}
        updateTeamList={updateTeamList}
        hasFetchedTeams={true}
        currentTeams={[
          { key: "frc254", team_number: 254, nickname: "Example" },
        ]}
        clearTeams={clearTeams}
        showErrorMessage={showErrorMessage}
      />
    );

    act(() => {
      ref.current.onTeamSelectionChanged(["254 | Example Team"]);
    });

    const button = screen.getByText(/Remove Team/i);
    expect(button).toBeEnabled();

    fireEvent.click(button);

    expect(updateTeamList).toHaveBeenCalledTimes(1);
    const callArgs = updateTeamList.mock.calls[0];
    expect(callArgs[0]).toEqual([]);

    ref.current.teamTypeahead = { getInstance: () => ({ clear: jest.fn() }) };

    const successCallback = callArgs[1];
    act(() => {
      successCallback();
    });

    await waitFor(() => expect(clearTeams).toHaveBeenCalledTimes(1));
    expect(button.className).toContain("btn-success");
  });

  test("buttons disabled and showErrorMessage when hasFetchedTeams is false", () => {
    const updateTeamList = jest.fn();
    const showErrorMessage = jest.fn();

    render(
      <AddRemoveSingleTeam
        selectedEvent={"event1"}
        updateTeamList={updateTeamList}
        hasFetchedTeams={false}
        currentTeams={[]}
        showErrorMessage={showErrorMessage}
      />
    );

    const addButton = screen.getByText(/Add Team/i);
    const removeButton = screen.getByText(/Remove Team/i);
    expect(addButton).toBeDisabled();
    expect(removeButton).toBeDisabled();
  });
});
