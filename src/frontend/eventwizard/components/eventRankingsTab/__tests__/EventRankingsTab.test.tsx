/**
 * @jest-environment jsdom
 */

import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventRankingsTab from "../EventRankingsTab";

jest.mock("../../../utils/rankingsParser");

describe("EventRankingsTab", () => {
  const mockMakeTrustedRequest = jest.fn().mockResolvedValue({
    ok: true,
    json: async () => ({}),
  } as Response);

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the main tab structure", () => {
    render(
      <EventRankingsTab
        selectedEvent="2024casj"
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    expect(screen.getByText("FMS Rankings Import")).toBeInTheDocument();
    expect(screen.getByText("Upload FMS Rankings Report")).toBeInTheDocument();
  });

  it("disables file input when no event is selected", () => {
    render(
      <EventRankingsTab
        selectedEvent=""
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    const fileInput = screen.getByLabelText("FMS Rankings Excel File");
    expect(fileInput).toBeDisabled();
  });

  it("enables file input when event is selected", () => {
    render(
      <EventRankingsTab
        selectedEvent="2024casj"
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    const fileInput = screen.getByLabelText("FMS Rankings Excel File");
    expect(fileInput).not.toBeDisabled();
  });
});
