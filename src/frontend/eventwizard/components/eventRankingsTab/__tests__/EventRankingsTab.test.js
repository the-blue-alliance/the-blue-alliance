/**
 * @jest-environment jsdom
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventRankingsTab from "../EventRankingsTab";
import { parseRankingsFile } from "../../../utils/rankingsParser";

jest.mock("../../../utils/rankingsParser");

describe("EventRankingsTab", () => {
  const mockMakeTrustedRequest = jest.fn();

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

  it("parses and displays rankings when file is selected", async () => {
    const mockRankings = [
      {
        team_key: "frc254",
        rank: 1,
        wins: 10,
        losses: 2,
        ties: 0,
        played: 12,
        dqs: 0,
        RS: 3.25,
        "Auto Pts": 45.2,
      },
      {
        team_key: "frc1323",
        rank: 2,
        wins: 9,
        losses: 3,
        ties: 0,
        played: 12,
        dqs: 0,
        RS: 3.1,
        "Auto Pts": 42.8,
      },
    ];

    parseRankingsFile.mockResolvedValue({
      rankings: mockRankings,
      headers: ["Rank", "Team", "RS", "Auto Pts", "W-L-T", "DQ", "Played"],
      breakdowns: ["RS", "Auto Pts"],
    });

    render(
      <EventRankingsTab
        selectedEvent="2024casj"
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    const file = new File([""], "rankings.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    const fileInput = screen.getByLabelText("FMS Rankings Excel File");

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Rankings Preview")).toBeInTheDocument();
    });

    // Check that rankings are displayed
    expect(screen.getByText("254")).toBeInTheDocument();
    expect(screen.getByText("1323")).toBeInTheDocument();
    expect(screen.getByText("3.25")).toBeInTheDocument();
    expect(screen.getByText("45.2")).toBeInTheDocument();
  });

  it("displays error message when file parsing fails", async () => {
    parseRankingsFile.mockRejectedValue(
      new Error("Could not find required columns")
    );

    render(
      <EventRankingsTab
        selectedEvent="2024casj"
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    const file = new File([""], "rankings.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    const fileInput = screen.getByLabelText("FMS Rankings Excel File");

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(
        screen.getByText(/Error parsing file: Could not find required columns/)
      ).toBeInTheDocument();
    });
  });

  it("uploads rankings when submit button is clicked", async () => {
    const mockRankings = [
      {
        team_key: "frc254",
        rank: 1,
        wins: 10,
        losses: 2,
        ties: 0,
        played: 12,
        dqs: 0,
        RS: 3.25,
      },
    ];

    parseRankingsFile.mockResolvedValue({
      rankings: mockRankings,
      headers: ["Rank", "Team", "RS", "W-L-T", "DQ", "Played"],
      breakdowns: ["RS"],
    });

    mockMakeTrustedRequest.mockImplementation(
      (path, data, onSuccess, onError) => {
        onSuccess();
      }
    );

    render(
      <EventRankingsTab
        selectedEvent="2024casj"
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    const file = new File([""], "rankings.xlsx");
    const fileInput = screen.getByLabelText("FMS Rankings Excel File");

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Rankings Preview")).toBeInTheDocument();
    });

    const submitButton = screen.getByText("Upload Rankings to TBA");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
        "/api/trusted/v1/event/2024casj/rankings/update",
        JSON.stringify({
          breakdowns: ["RS"],
          rankings: mockRankings,
        }),
        expect.any(Function),
        expect.any(Function)
      );
    });

    await waitFor(() => {
      expect(
        screen.getByText("Rankings uploaded successfully!")
      ).toBeInTheDocument();
    });
  });

  it("displays error message when upload fails", async () => {
    const mockRankings = [
      {
        team_key: "frc254",
        rank: 1,
        wins: 10,
        losses: 2,
        ties: 0,
        played: 12,
        dqs: 0,
        RS: 3.25,
      },
    ];

    parseRankingsFile.mockResolvedValue({
      rankings: mockRankings,
      headers: ["Rank", "Team", "RS", "W-L-T", "DQ", "Played"],
      breakdowns: ["RS"],
    });

    mockMakeTrustedRequest.mockImplementation(
      (path, data, onSuccess, onError) => {
        onError("Network error");
      }
    );

    render(
      <EventRankingsTab
        selectedEvent="2024casj"
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    const file = new File([""], "rankings.xlsx");
    const fileInput = screen.getByLabelText("FMS Rankings Excel File");

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Rankings Preview")).toBeInTheDocument();
    });

    const submitButton = screen.getByText("Upload Rankings to TBA");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText("Error uploading rankings: Network error")
      ).toBeInTheDocument();
    });
  });

  it("shows W-L-T record correctly in preview", async () => {
    const mockRankings = [
      {
        team_key: "frc254",
        rank: 1,
        wins: 10,
        losses: 2,
        ties: 1,
        played: 13,
        dqs: 0,
        RS: 3.25,
      },
    ];

    parseRankingsFile.mockResolvedValue({
      rankings: mockRankings,
      headers: ["Rank", "Team", "RS", "W-L-T", "DQ", "Played"],
      breakdowns: ["RS"],
    });

    render(
      <EventRankingsTab
        selectedEvent="2024casj"
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    const file = new File([""], "rankings.xlsx");
    const fileInput = screen.getByLabelText("FMS Rankings Excel File");

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("10-2-1")).toBeInTheDocument();
    });
  });

  it("disables submit button while uploading", async () => {
    const mockRankings = [
      {
        team_key: "frc254",
        rank: 1,
        wins: 10,
        losses: 2,
        ties: 0,
        played: 12,
        dqs: 0,
        RS: 3.25,
      },
    ];

    parseRankingsFile.mockResolvedValue({
      rankings: mockRankings,
      headers: ["Rank", "Team", "RS", "W-L-T", "DQ", "Played"],
      breakdowns: ["RS"],
    });

    let resolveRequest;
    mockMakeTrustedRequest.mockImplementation(
      (path, data, onSuccess, onError) => {
        return new Promise((resolve) => {
          resolveRequest = () => {
            onSuccess();
            resolve();
          };
        });
      }
    );

    render(
      <EventRankingsTab
        selectedEvent="2024casj"
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

    const file = new File([""], "rankings.xlsx");
    const fileInput = screen.getByLabelText("FMS Rankings Excel File");

    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Rankings Preview")).toBeInTheDocument();
    });

    const submitButton = screen.getByText("Upload Rankings to TBA");
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Uploading...")).toBeInTheDocument();
      expect(submitButton).toBeDisabled();
    });
  });
});
