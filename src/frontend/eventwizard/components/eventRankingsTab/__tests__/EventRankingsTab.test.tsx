/**
 * @jest-environment jsdom
 */

import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import EventRankingsTab from "../EventRankingsTab";
import { parseRankingsFile, RankingsResult } from "../../../utils/rankingsParser";
import { uploadFmsReport } from "../../../utils/fmsReportUpload";

jest.mock("../../../utils/rankingsParser");
jest.mock("../../../utils/fmsReportUpload");

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

describe("EventRankingsTab interactions", () => {
  const mockParseRankingsFile = parseRankingsFile as jest.Mock;
  const mockUploadFmsReport = uploadFmsReport as jest.Mock;
  const mockMakeTrustedRequest = jest.fn();
  const selectedEvent = "2024casj";
  const file = new File(["rankings"], "2024casj_RankingsReport.xlsx");

  const parsed: RankingsResult = {
    headers: ["Rank", "Team", "W-L-T", "DQ", "Played", "Qual Avg", "Avg Coop"],
    breakdowns: ["Qual Avg", "Avg Coop"],
    rankings: [
      {
        team_key: "frc254",
        rank: 1,
        wins: 8,
        losses: 1,
        ties: 0,
        played: 9,
        dqs: 0,
        "Qual Avg": 3.2,
        "Avg Coop": 1.5,
      },
      {
        team_key: "frc1114",
        rank: 2,
        wins: 7,
        losses: 2,
        ties: 0,
        played: 9,
        dqs: 1,
        "Qual Avg": 2.9,
        // "Avg Coop" intentionally missing to exercise the empty-cell fallback
      },
    ],
  };

  const renderTab = (event = selectedEvent) =>
    render(
      <EventRankingsTab
        selectedEvent={event}
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );

  const fileInput = () =>
    screen.getByLabelText("FMS Rankings Excel File") as HTMLInputElement;

  const loadFile = async (): Promise<void> => {
    fireEvent.change(fileInput(), { target: { files: [file] } });
    await screen.findByText(
      "Loaded rankings for 2 teams with 2 breakdown columns"
    );
  };

  beforeEach(() => {
    mockParseRankingsFile.mockResolvedValue(parsed);
    mockUploadFmsReport.mockResolvedValue(undefined);
    mockMakeTrustedRequest.mockResolvedValue({ ok: true } as Response);
    window.alert = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("ignores a change event that carries no file", () => {
    renderTab();

    fireEvent.change(fileInput(), { target: { files: [] } });

    expect(mockParseRankingsFile).not.toHaveBeenCalled();
    expect(screen.queryByText(/Loading rankings/)).not.toBeInTheDocument();
  });

  it("parses the file and previews every column, mapping fields back to headers", async () => {
    renderTab();

    await loadFile();

    expect(mockParseRankingsFile).toHaveBeenCalledWith(file);
    expect(screen.getByText("Rankings Preview")).toBeInTheDocument();
    expect(
      screen.getAllByRole("columnheader").map((th) => th.textContent)
    ).toEqual(parsed.headers);
    const rows = screen.getAllByRole("row").slice(1);
    expect(
      rows.map((row) =>
        Array.from(row.querySelectorAll("td")).map((td) => td.textContent)
      )
    ).toEqual([
      ["1", "254", "8-1-0", "0", "9", "3.2", "1.5"],
      ["2", "1114", "7-2-0", "1", "9", "2.9", ""],
    ]);
    expect(screen.getByText(/Loaded rankings/)).toHaveClass("alert-info");
  });

  it("previews the rank instead of the value for breakdown columns whose name contains 'rank'", async () => {
    // Documents current behaviour: the preview maps headers to fields by
    // substring, so FMS's "Ranking Score" breakdown column is shown as the
    // team's rank. The uploaded payload is unaffected.
    mockParseRankingsFile.mockResolvedValue({
      ...parsed,
      headers: ["Rank", "Team", "Ranking Score"],
      breakdowns: ["Ranking Score"],
      rankings: [{ ...parsed.rankings[0], "Ranking Score": 3.2 }],
    });
    renderTab();

    fireEvent.change(fileInput(), { target: { files: [file] } });
    await screen.findByText("Loaded rankings for 1 teams with 1 breakdown columns");

    expect(screen.getAllByRole("cell").map((td) => td.textContent)).toEqual([
      "1",
      "254",
      "1",
    ]);
  });

  it("supports a WLT record header as well as W-L-T", async () => {
    mockParseRankingsFile.mockResolvedValue({
      ...parsed,
      headers: ["Rank", "Team", "WLT"],
    });
    renderTab();

    await loadFile();

    expect(screen.getAllByRole("cell").map((td) => td.textContent)).toEqual([
      "1",
      "254",
      "8-1-0",
      "2",
      "1114",
      "7-2-0",
    ]);
  });

  it("shows a danger alert and clears the preview when parsing fails", async () => {
    renderTab();
    await loadFile();
    mockParseRankingsFile.mockRejectedValueOnce(new Error("bad workbook"));

    fireEvent.change(fileInput(), { target: { files: [file] } });

    const alert = await screen.findByText("Error parsing file: bad workbook");
    expect(alert).toHaveClass("alert-danger");
    expect(screen.queryByText("Rankings Preview")).not.toBeInTheDocument();
  });

  it("uploads the rankings then archives the report", async () => {
    renderTab();
    await loadFile();

    fireEvent.click(screen.getByRole("button", { name: "Upload Rankings to TBA" }));

    const success = await screen.findByText("Rankings uploaded successfully!");
    expect(success).toHaveClass("alert-success");
    expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
      "/api/trusted/v1/event/2024casj/rankings/update",
      JSON.stringify({
        breakdowns: parsed.breakdowns,
        rankings: parsed.rankings,
      })
    );
    expect(mockUploadFmsReport).toHaveBeenCalledWith(
      file,
      selectedEvent,
      "qual_rankings",
      mockMakeTrustedRequest
    );
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Upload Rankings to TBA" })
      ).toBeEnabled();
    });
  });

  it("shows the upload error and re-enables the button", async () => {
    mockMakeTrustedRequest.mockRejectedValueOnce(new Error("boom"));
    renderTab();
    await loadFile();

    fireEvent.click(screen.getByRole("button", { name: "Upload Rankings to TBA" }));

    expect(
      await screen.findByText("Error uploading rankings: Error: boom")
    ).toBeInTheDocument();
    expect(mockUploadFmsReport).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Upload Rankings to TBA" })
    ).toBeEnabled();
  });

  it("refuses to upload when the selected event has been cleared", async () => {
    const { rerender } = renderTab();
    await loadFile();

    rerender(
      <EventRankingsTab
        selectedEvent=""
        makeTrustedRequest={mockMakeTrustedRequest}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: "Upload Rankings to TBA" }));

    expect(window.alert).toHaveBeenCalledWith("Please select an event first");
    expect(mockMakeTrustedRequest).not.toHaveBeenCalled();
  });
});
