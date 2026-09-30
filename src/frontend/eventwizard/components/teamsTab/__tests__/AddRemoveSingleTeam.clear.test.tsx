/* @jest-environment jsdom */
import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import AddRemoveSingleTeam from "../AddRemoveSingleTeam";

// The real AsyncSelect is not clearable, so it never emits a null selection.
// Stub it so the component's null-selection handling can still be exercised.
jest.mock("react-select/async", () => ({
  __esModule: true,
  default: ({
    onChange,
  }: {
    onChange: (value: { value: string; label: string } | null) => void;
  }) => (
    <div>
      <button onClick={() => onChange({ value: "frc254", label: "254" })}>
        pick
      </button>
      <button onClick={() => onChange(null)}>clear</button>
    </div>
  ),
}));

describe("AddRemoveSingleTeam with a cleared selection", () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockResolvedValue({
      json: jest.fn().mockResolvedValue([]),
    });
  });

  it("disables Add again when the selection is cleared", async () => {
    render(
      <AddRemoveSingleTeam
        selectedEvent="2024nytr"
        updateTeamList={jest.fn()}
        hasFetchedTeams={true}
        currentTeams={[]}
        showErrorMessage={jest.fn()}
      />
    );
    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    const addButton = screen.getByRole("button", { name: "Add Team" });

    fireEvent.click(screen.getByText("pick"));
    expect(addButton).toBeEnabled();

    fireEvent.click(screen.getByText("clear"));
    expect(addButton).toBeDisabled();
  });
});
