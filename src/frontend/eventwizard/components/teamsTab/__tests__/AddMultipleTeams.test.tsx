/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import {
  render,
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react";
import AddMultipleTeams from "../AddMultipleTeams";

describe("AddMultipleTeams", () => {
  const mockUpdateTeamList = jest.fn();
  const mockClearTeams = jest.fn();
  const mockShowErrorMessage = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("textarea input updates component state (controlled input)", () => {
    render(
      <AddMultipleTeams
        selectedEvent="event1"
        updateTeamList={mockUpdateTeamList}
        clearTeams={mockClearTeams}
        showErrorMessage={mockShowErrorMessage}
      />
    );

    const textarea = screen.getByRole("textbox");
    expect(textarea).toBeInTheDocument();

    fireEvent.change(textarea, { target: { value: "254\n1114" } });
    expect(textarea).toHaveValue("254\n1114");
  });

  test("clicking Overwrite calls updateTeamList with correct team keys", async () => {
    render(
      <AddMultipleTeams
        selectedEvent="event1"
        updateTeamList={mockUpdateTeamList}
        clearTeams={mockClearTeams}
        showErrorMessage={mockShowErrorMessage}
      />
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "254\n1114" } });

    const button = screen.getByText(/Overwrite Teams/i);
    expect(button).toBeEnabled();

    // Click the button which should call updateTeamList
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockUpdateTeamList).toHaveBeenCalledTimes(1);
    });

    // Validate that updateTeamList was called with the expected team ids
    const callArgs = mockUpdateTeamList.mock.calls[0];
    expect(callArgs[0]).toEqual(["frc254", "frc1114"]);
    expect(typeof callArgs[1]).toBe("function"); // success callback
    expect(typeof callArgs[2]).toBe("function"); // error callback
  });

  test("success callback sets button to success class and clears teams", async () => {
    mockUpdateTeamList.mockImplementation(
      (teams, successCallback) => {
        successCallback();
      }
    );

    render(
      <AddMultipleTeams
        selectedEvent="event1"
        updateTeamList={mockUpdateTeamList}
        clearTeams={mockClearTeams}
        showErrorMessage={mockShowErrorMessage}
      />
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "254\n1114" } });

    const button = screen.getByText(/Overwrite Teams/i);
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockClearTeams).toHaveBeenCalledTimes(1);
      expect(button.className).toContain("btn-success");
    });
  });

  test("shows error when invalid team number is entered", () => {
    render(
      <AddMultipleTeams
        selectedEvent="event1"
        updateTeamList={mockUpdateTeamList}
        showErrorMessage={mockShowErrorMessage}
      />
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "254\nabc\n1114" } });

    const button = screen.getByText(/Overwrite Teams/i);
    fireEvent.click(button);

    expect(mockShowErrorMessage).toHaveBeenCalledWith("Invalid team abc");
    expect(mockUpdateTeamList).not.toHaveBeenCalled();
  });

  test("disables button when no event is selected", () => {
    render(
      <AddMultipleTeams
        selectedEvent={null}
        updateTeamList={mockUpdateTeamList}
        showErrorMessage={mockShowErrorMessage}
      />
    );

    const button = screen.getByText(/Overwrite Teams/i);
    expect(button).toBeDisabled();
  });
});

describe("AddMultipleTeams failure reporting", () => {
  test("forwards update errors to showErrorMessage and keeps the pending class", () => {
    const updateTeamList = jest.fn((_teams, _onSuccess, onError) =>
      onError("Upload failed")
    );
    const showErrorMessage = jest.fn();
    const clearTeams = jest.fn();
    render(
      <AddMultipleTeams
        selectedEvent="event1"
        updateTeamList={updateTeamList}
        clearTeams={clearTeams}
        showErrorMessage={showErrorMessage}
      />
    );
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "254" } });

    fireEvent.click(screen.getByRole("button", { name: "Overwrite Teams" }));

    expect(updateTeamList).toHaveBeenCalledWith(
      ["frc254"],
      expect.any(Function),
      expect.any(Function)
    );
    expect(showErrorMessage).toHaveBeenCalledWith("Upload failed");
    expect(clearTeams).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Overwrite Teams" })).toHaveClass(
      "btn-warning"
    );
  });
});
