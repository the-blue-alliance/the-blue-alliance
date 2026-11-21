/* @jest-environment jsdom */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventSelector from "../EventSelector";

// EventSelector caches the fetched event list in a module-level variable, so
// the logged-out path has to be exercised in its own module registry.
describe("EventSelector when the user is not logged in", () => {
  it("offers only the Other option when the events request returns 401", async () => {
    const json = jest.fn();
    global.fetch = jest.fn().mockResolvedValue({ status: 401, json });

    render(
      <EventSelector
        manualEvent={false}
        setEvent={jest.fn()}
        setManualEvent={jest.fn()}
        clearAuth={jest.fn()}
      />
    );

    fireEvent.keyDown(screen.getByRole("combobox"), {
      key: "ArrowDown",
      keyCode: 40,
    });

    expect(await screen.findByText("Other")).toBeInTheDocument();
    expect(json).not.toHaveBeenCalled();
    expect(screen.getAllByRole("option")).toHaveLength(1);
  });
});
