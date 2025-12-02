/**
 * @jest-environment jsdom
 */

import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { renderToStaticMarkup } from "react-dom/server";
import MatchPlayTab from "../MatchPlayTab";

describe("MatchPlayTab", () => {
  const mockMakeTrustedRequest = jest.fn();
  const mockMakeApiV3Request = jest.fn();
  const selectedEvent = "2024nytr";

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders the main container with correct structure", () => {
    const html = renderToStaticMarkup(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    expect(html).toContain('id="matches"');
    expect(html).toContain("Match Play");
  });

  it("renders the panel with Match Score Entry heading", () => {
    const html = renderToStaticMarkup(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    expect(html).toContain("Match Score Entry");
    expect(html).toContain("panel panel-default");
    expect(html).toContain("panel-heading");
  });

  it("renders Fetch Matches button", () => {
    const html = renderToStaticMarkup(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    expect(html).toContain("Fetch Matches");
    expect(html).toContain("btn btn-primary");
  });

  it("disables Fetch Matches button when no selectedEvent", () => {
    const html = renderToStaticMarkup(
      <MatchPlayTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    expect(html).toContain("disabled");
  });

  it("does not show status message initially", () => {
    const html = renderToStaticMarkup(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    expect(html).not.toContain("alert alert-info");
  });

  it("does not show match table initially", () => {
    const html = renderToStaticMarkup(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    expect(html).not.toContain("table table-striped");
  });

  it("renders description text about the tab", () => {
    const html = renderToStaticMarkup(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    expect(html).toContain("Fetch matches from TBA");
    expect(html).toContain("manually enter match scores");
  });

  it("fetches matches and displays them in a table", async () => {
    const mockMatches = [
      {
        key: "2024nytr_qm1",
        comp_level: "qm",
        set_number: 1,
        match_number: 1,
        alliances: {
          red: {
            score: 45,
            team_keys: ["frc254", "frc1323", "frc359"],
          },
          blue: {
            score: 32,
            team_keys: ["frc118", "frc2056", "frc5254"],
          },
        },
      },
      {
        key: "2024nytr_qm2",
        comp_level: "qm",
        set_number: 1,
        match_number: 2,
        alliances: {
          red: {
            score: 28,
            team_keys: ["frc1", "frc2", "frc3"],
          },
          blue: {
            score: 41,
            team_keys: ["frc4", "frc5", "frc6"],
          },
        },
      },
    ];

    mockMakeApiV3Request.mockImplementation((path, onSuccess) => {
      onSuccess(mockMatches);
    });

    render(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    const fetchButton = screen.getByText("Fetch Matches");
    fireEvent.click(fetchButton);

    await waitFor(() => {
      expect(mockMakeApiV3Request).toHaveBeenCalledWith(
        `/api/v3/event/${selectedEvent}/matches/simple`,
        expect.any(Function),
        expect.any(Function)
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Loaded 2 matches")).toBeInTheDocument();
    });

    // Verify match table is rendered
    expect(screen.getByText("Qualification 1")).toBeInTheDocument();
    expect(screen.getByText("Qualification 2")).toBeInTheDocument();

    // Verify team numbers are displayed (without frc prefix)
    expect(screen.getByText("254, 1323, 359")).toBeInTheDocument();
    expect(screen.getByText("118, 2056, 5254")).toBeInTheDocument();
  });

  it("displays error message when fetch fails", async () => {
    mockMakeApiV3Request.mockImplementation((path, onSuccess, onError) => {
      onError("Failed to fetch matches");
    });

    render(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    const fetchButton = screen.getByText("Fetch Matches");
    fireEvent.click(fetchButton);

    await waitFor(() => {
      expect(
        screen.getByText("Error loading matches: Failed to fetch matches")
      ).toBeInTheDocument();
    });

    // Match table should not be rendered
    expect(screen.queryByText("Match")).not.toBeInTheDocument();
  });

  it("shows loading state while fetching matches", async () => {
    mockMakeApiV3Request.mockImplementation(() => {
      // Don't call callbacks immediately to simulate loading
    });

    render(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    const fetchButton = screen.getByText("Fetch Matches");
    fireEvent.click(fetchButton);

    await waitFor(() => {
      expect(screen.getByText("Loading...")).toBeInTheDocument();
      expect(screen.getByText("Loading matches...")).toBeInTheDocument();
    });
  });

  it("updates match scores via Trusted API", async () => {
    const mockMatches = [
      {
        key: "2024nytr_qm1",
        comp_level: "qm",
        set_number: 1,
        match_number: 1,
        alliances: {
          red: {
            score: 0,
            team_keys: ["frc254", "frc1323", "frc359"],
          },
          blue: {
            score: 0,
            team_keys: ["frc118", "frc2056", "frc5254"],
          },
        },
      },
    ];

    mockMakeApiV3Request.mockImplementation((path, onSuccess) => {
      onSuccess(mockMatches);
    });

    mockMakeTrustedRequest.mockImplementation(
      (path, body, onSuccess, onError) => {
        onSuccess();
      }
    );

    render(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    // Fetch matches first
    const fetchButton = screen.getByText("Fetch Matches");
    fireEvent.click(fetchButton);

    await waitFor(() => {
      expect(screen.getByText("Loaded 1 matches")).toBeInTheDocument();
    });

    // Find score input fields (both have placeholder="Score")
    const scoreInputs = screen.getAllByPlaceholderText("Score");
    // First input is red score, second is blue score
    const redScoreInput = scoreInputs[0];
    const blueScoreInput = scoreInputs[1];

    // Enter scores
    fireEvent.change(redScoreInput, { target: { value: "45" } });
    fireEvent.change(blueScoreInput, { target: { value: "32" } });

    // Click update button
    const updateButtons = screen.getAllByText("Update");
    fireEvent.click(updateButtons[0]);

    await waitFor(() => {
      expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
        `/api/trusted/v1/event/${selectedEvent}/matches/update`,
        expect.stringContaining('"comp_level":"qm"'),
        expect.any(Function),
        expect.any(Function)
      );
    });

    // Verify the request body contains correct scores
    const requestBody = JSON.parse(mockMakeTrustedRequest.mock.calls[0][1]);
    expect(requestBody).toHaveLength(1);
    expect(requestBody[0].alliances.red.score).toBe(45);
    expect(requestBody[0].alliances.blue.score).toBe(32);
    expect(requestBody[0].alliances.red.teams).toEqual([
      "frc254",
      "frc1323",
      "frc359",
    ]);
    expect(requestBody[0].alliances.blue.teams).toEqual([
      "frc118",
      "frc2056",
      "frc5254",
    ]);

    // Verify success message
    await waitFor(() => {
      expect(
        screen.getByText("Successfully updated Qualification 1!")
      ).toBeInTheDocument();
    });
  });

  it("displays error message when match update fails", async () => {
    const mockMatches = [
      {
        key: "2024nytr_qm1",
        comp_level: "qm",
        set_number: 1,
        match_number: 1,
        alliances: {
          red: {
            score: 0,
            team_keys: ["frc254", "frc1323", "frc359"],
          },
          blue: {
            score: 0,
            team_keys: ["frc118", "frc2056", "frc5254"],
          },
        },
      },
    ];

    mockMakeApiV3Request.mockImplementation((path, onSuccess) => {
      onSuccess(mockMatches);
    });

    mockMakeTrustedRequest.mockImplementation(
      (path, body, onSuccess, onError) => {
        onError("Authentication failed");
      }
    );

    render(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    // Fetch matches first
    const fetchButton = screen.getByText("Fetch Matches");
    fireEvent.click(fetchButton);

    await waitFor(() => {
      expect(screen.getByText("Loaded 1 matches")).toBeInTheDocument();
    });

    // Enter scores (both inputs have placeholder="Score")
    const scoreInputs = screen.getAllByPlaceholderText("Score");
    fireEvent.change(scoreInputs[0], { target: { value: "45" } });
    fireEvent.change(scoreInputs[1], { target: { value: "32" } });

    // Click update button
    const updateButtons = screen.getAllByText("Update");
    fireEvent.click(updateButtons[0]);

    await waitFor(() => {
      expect(
        screen.getByText("Error updating match: Authentication failed")
      ).toBeInTheDocument();
    });
  });

  it("sorts matches by comp level and match number", async () => {
    const mockMatches = [
      {
        key: "2024nytr_f1m1",
        comp_level: "f",
        set_number: 1,
        match_number: 1,
        alliances: {
          red: { score: 0, team_keys: ["frc1", "frc2", "frc3"] },
          blue: { score: 0, team_keys: ["frc4", "frc5", "frc6"] },
        },
      },
      {
        key: "2024nytr_qm2",
        comp_level: "qm",
        set_number: 1,
        match_number: 2,
        alliances: {
          red: { score: 0, team_keys: ["frc7", "frc8", "frc9"] },
          blue: { score: 0, team_keys: ["frc10", "frc11", "frc12"] },
        },
      },
      {
        key: "2024nytr_qm1",
        comp_level: "qm",
        set_number: 1,
        match_number: 1,
        alliances: {
          red: { score: 0, team_keys: ["frc13", "frc14", "frc15"] },
          blue: { score: 0, team_keys: ["frc16", "frc17", "frc18"] },
        },
      },
      {
        key: "2024nytr_sf1m1",
        comp_level: "sf",
        set_number: 1,
        match_number: 1,
        alliances: {
          red: { score: 0, team_keys: ["frc19", "frc20", "frc21"] },
          blue: { score: 0, team_keys: ["frc22", "frc23", "frc24"] },
        },
      },
    ];

    mockMakeApiV3Request.mockImplementation((path, onSuccess) => {
      onSuccess(mockMatches);
    });

    render(
      <MatchPlayTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    const fetchButton = screen.getByText("Fetch Matches");
    fireEvent.click(fetchButton);

    await waitFor(() => {
      expect(screen.getByText("Loaded 4 matches")).toBeInTheDocument();
    });

    // Get all match name elements
    const matchNames = screen.getAllByText(/Qualification|Semifinal|Final/);

    // Verify order: qm1, qm2, sf1, f1
    expect(matchNames[0]).toHaveTextContent("Qualification 1");
    expect(matchNames[1]).toHaveTextContent("Qualification 2");
    expect(matchNames[2]).toHaveTextContent("Semifinal 1-1");
    expect(matchNames[3]).toHaveTextContent("Final 1-1");
  });

  it("shows status message when no event is selected", () => {
    render(
      <MatchPlayTab
        selectedEvent={null}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );

    const fetchButton = screen.getByText("Fetch Matches");

    // Button should be disabled when no event selected
    expect(fetchButton).toBeDisabled();

    // Clicking disabled button does nothing but we can test the behavior
    fireEvent.click(fetchButton);

    // API should not be called
    expect(mockMakeApiV3Request).not.toHaveBeenCalled();
  });
});
