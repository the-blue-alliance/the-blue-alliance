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
import AddMultipleTeams from "../AddMultipleTeams";

describe("AddMultipleTeams", () => {
  test("textarea input updates component state (controlled input)", () => {
    const updateTeamList = jest.fn();
    const showErrorMessage = jest.fn();

    render(
      <AddMultipleTeams
        selectedEvent={"event1"}
        updateTeamList={updateTeamList}
        showErrorMessage={showErrorMessage}
      />
    );

    const textarea = screen.getByRole("textbox");
    expect(textarea).toBeInTheDocument();

    fireEvent.change(textarea, { target: { value: "254\n1114" } });
    expect(textarea.value).toBe("254\n1114");
  });

  test("clicking Overwrite calls updateTeamList and clearTeams on success", async () => {
    const updateTeamList = jest.fn();
    const clearTeams = jest.fn();
    const showErrorMessage = jest.fn();

    render(
      <AddMultipleTeams
        selectedEvent={"event1"}
        updateTeamList={updateTeamList}
        clearTeams={clearTeams}
        showErrorMessage={showErrorMessage}
      />
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "254\n1114" } });

    const button = screen.getByText(/Overwrite Teams/i);
    expect(button).toBeEnabled();

    // Click the button which should call updateTeamList
    fireEvent.click(button);

    expect(updateTeamList).toHaveBeenCalledTimes(1);

    // Validate that updateTeamList was called with the expected team ids
    const callArgs = updateTeamList.mock.calls[0];
    expect(callArgs[0]).toEqual(["frc254", "frc1114"]);

    // Simulate success callback being run by the API implementation
    const successCallback = callArgs[1];
    expect(typeof successCallback).toBe("function");

    // The component will set the button class to btn-warning immediately,
    // and to btn-success inside the success callback. Call it wrapped in act and wait.
    act(() => {
      successCallback();
    });

    await waitFor(() => expect(clearTeams).toHaveBeenCalledTimes(1));

    // After success callback, button should have the success class
    expect(button.className).toContain("btn-success");
  });
});
