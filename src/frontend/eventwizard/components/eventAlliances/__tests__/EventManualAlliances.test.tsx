/**
 * @jest-environment jsdom
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventManualAlliances from "../EventManualAlliances";

describe("EventManualAlliances", () => {
  const alliances = Array.from({ length: 8 }, (_, i) => ({
    captain: i === 0 ? "254" : "",
    pick1: "",
    pick2: "",
    pick3: "",
  }));
  const onAllianceSizeChange = jest.fn();
  const onAllianceChange = jest.fn();
  const onSubmit = jest.fn();

  const renderComponent = (
    overrides: Partial<React.ComponentProps<typeof EventManualAlliances>> = {}
  ) =>
    render(
      <EventManualAlliances
        allianceSize={4}
        alliances={alliances}
        uploading={false}
        selectedEvent="2025nysu"
        onAllianceSizeChange={onAllianceSizeChange}
        onAllianceChange={onAllianceChange}
        onSubmit={onSubmit}
        {...overrides}
      />
    );

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("reports edits to every field with the alliance index and field name", () => {
    renderComponent();

    fireEvent.change(screen.getByPlaceholderText("Captain 3"), {
      target: { value: "1" },
    });
    fireEvent.change(screen.getByPlaceholderText("Pick 3-1"), {
      target: { value: "2" },
    });
    fireEvent.change(screen.getByPlaceholderText("Pick 3-2"), {
      target: { value: "3" },
    });
    fireEvent.change(screen.getByPlaceholderText("Pick 3-3"), {
      target: { value: "4" },
    });

    expect(onAllianceChange.mock.calls).toEqual([
      [2, "captain", "1"],
      [2, "pick1", "2"],
      [2, "pick2", "3"],
      [2, "pick3", "4"],
    ]);
  });

  it("renders the current values and forwards size changes and submits", () => {
    renderComponent();

    expect(screen.getByPlaceholderText("Captain 1")).toHaveValue("254");
    expect(screen.getByRole("radio", { name: "4" })).toBeChecked();

    fireEvent.click(screen.getByRole("radio", { name: "3" }));
    expect(onAllianceSizeChange).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "Upload Alliances to TBA" }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("disables inputs while uploading and styles the status message", () => {
    renderComponent({ uploading: true, statusMessage: "Uploading alliances..." });

    expect(screen.getByPlaceholderText("Captain 1")).toBeDisabled();
    expect(screen.getByPlaceholderText("Pick 1-3")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Uploading..." })).toBeDisabled();
    expect(screen.getByText("Uploading alliances...")).toHaveClass("alert-info");
  });
});
