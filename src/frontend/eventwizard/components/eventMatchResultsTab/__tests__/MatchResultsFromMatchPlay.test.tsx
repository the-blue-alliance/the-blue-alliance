/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import MatchResultsFromMatchPlay from "../MatchResultsFromMatchPlay";

describe("MatchResultsFromMatchPlay", () => {
  const mockMakeTrustedRequest = jest.fn<Promise<Response>, [string, string]>();
  const mockMakeApiV3Request = jest.fn<Promise<Response>, [string]>();
  const selectedEvent = "2024nytr";

  const makeJsonResponse = (payload: unknown): Response =>
    ({
      ok: true,
      statusText: "OK",
      json: async () => payload,
    } as Response);

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Fetching Matches", () => {
    it("requests the simple matches endpoint when Fetch Matches is clicked", async () => {
      mockMakeApiV3Request.mockResolvedValue(makeJsonResponse([]));

      render(
        <MatchResultsFromMatchPlay
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /Fetch Matches/i }));

      await waitFor(() => {
        expect(mockMakeApiV3Request).toHaveBeenCalledWith(
          `/api/v3/event/${selectedEvent}/matches/simple`
        );
      });
    });

    it("parses the JSON body and renders matches after a successful fetch", async () => {
      const mockMatches = [
        {
          key: "2024nytr_qm2",
          comp_level: "qm",
          set_number: 1,
          match_number: 2,
          alliances: {
            red: { team_keys: ["frc254", "frc971", "frc1678"], score: 110 },
            blue: { team_keys: ["frc1323", "frc2056", "frc5499"], score: 95 },
          },
        },
        {
          key: "2024nytr_qm1",
          comp_level: "qm",
          set_number: 1,
          match_number: 1,
          alliances: {
            red: { team_keys: ["frc254", "frc971", "frc1678"], score: 100 },
            blue: { team_keys: ["frc1323", "frc2056", "frc5499"], score: 90 },
          },
        },
      ];

      mockMakeApiV3Request.mockResolvedValue(makeJsonResponse(mockMatches));

      render(
        <MatchResultsFromMatchPlay
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /Fetch Matches/i }));

      await waitFor(() => {
        expect(screen.getByText("Qualification 1")).toBeInTheDocument();
        expect(screen.getByText("Qualification 2")).toBeInTheDocument();
      });

      expect(screen.getByText("Loaded 2 matches")).toBeInTheDocument();

      // Matches render in sorted play order — Qualification 1 before Qualification 2.
      const matchRows = screen.getAllByRole("row");
      const headerAndRows = matchRows.map((row) => row.textContent || "");
      const qm1Index = headerAndRows.findIndex((t) => t.includes("Qualification 1"));
      const qm2Index = headerAndRows.findIndex((t) => t.includes("Qualification 2"));
      expect(qm1Index).toBeLessThan(qm2Index);
    });

    it("shows an error when the matches response is not an array", async () => {
      mockMakeApiV3Request.mockResolvedValue(makeJsonResponse({ matches: [] }));

      render(
        <MatchResultsFromMatchPlay
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /Fetch Matches/i }));

      await waitFor(() => {
        expect(screen.getByText(/Error loading matches:/)).toBeInTheDocument();
        expect(
          screen.getByText(/Unexpected matches response format/)
        ).toBeInTheDocument();
      });
    });

    it("surfaces a friendly error when the request fails with a non-2xx status", async () => {
      mockMakeApiV3Request.mockResolvedValue({
        ok: false,
        statusText: "Not Found",
        json: async () => ({}),
      } as Response);

      render(
        <MatchResultsFromMatchPlay
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /Fetch Matches/i }));

      await waitFor(() => {
        expect(screen.getByText(/Error loading matches:/)).toBeInTheDocument();
        expect(screen.getByText(/Not Found/)).toBeInTheDocument();
      });
    });
  });

  describe("Updating Matches", () => {
    const mockMatches = [
      {
        key: "2024nytr_qm1",
        comp_level: "qm",
        set_number: 1,
        match_number: 1,
        alliances: {
          red: { team_keys: ["frc254"], score: 100 },
          blue: { team_keys: ["frc1323"], score: 90 },
        },
      },
    ];

    const renderAndFetch = async () => {
      mockMakeApiV3Request.mockResolvedValue(makeJsonResponse(mockMatches));

      render(
        <MatchResultsFromMatchPlay
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /Fetch Matches/i }));

      await waitFor(() => {
        expect(screen.getByText("Qualification 1")).toBeInTheDocument();
      });
    };

    it("posts the match update and reports success", async () => {
      await renderAndFetch();

      mockMakeTrustedRequest.mockResolvedValueOnce(makeJsonResponse({}));

      fireEvent.click(screen.getByRole("button", { name: /^Update$/i }));

      await waitFor(() => {
        expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
          `/api/trusted/v1/event/${selectedEvent}/matches/update`,
          JSON.stringify([
            {
              comp_level: "qm",
              set_number: 1,
              match_number: 1,
              alliances: {
                red: { teams: ["frc254"], score: 100 },
                blue: { teams: ["frc1323"], score: 90 },
              },
            },
          ])
        );
      });

      await waitFor(() => {
        expect(
          screen.getByText(/Successfully updated Qualification 1/)
        ).toBeInTheDocument();
      });
    });

    it("reports an error and re-enables the row when the update request fails", async () => {
      await renderAndFetch();

      mockMakeTrustedRequest.mockRejectedValueOnce(new Error("Unauthorized"));

      fireEvent.click(screen.getByRole("button", { name: /^Update$/i }));

      await waitFor(() => {
        expect(
          screen.getByText(/Error updating match:.*Unauthorized/)
        ).toBeInTheDocument();
      });

      // Button returns to its idle state so the user can retry.
      expect(screen.getByRole("button", { name: /^Update$/i })).toBeEnabled();
    });
  });
});

describe("MatchResultsFromMatchPlay ordering and score entry", () => {
  const mockMakeTrustedRequest = jest.fn<Promise<Response>, [string, string]>();
  const mockMakeApiV3Request = jest.fn<Promise<Response>, [string]>();
  const selectedEvent = "2024nytr";

  const makeJsonResponse = (payload: unknown): Response =>
    ({ ok: true, statusText: "OK", json: async () => payload }) as Response;

  const makeMatch = (
    key: string,
    comp_level: string,
    set_number: number,
    match_number: number,
    scores: { red?: number; blue?: number } = {}
  ) => ({
    key: `${selectedEvent}_${key}`,
    comp_level,
    set_number,
    match_number,
    alliances: {
      red: { team_keys: ["frc254", "frc971", "frc1678"], score: scores.red },
      blue: { team_keys: ["frc1323", "frc2056", "frc5499"], score: scores.blue },
    },
  });

  const renderAndFetch = async (matches: unknown[]): Promise<void> => {
    mockMakeApiV3Request.mockResolvedValue(makeJsonResponse(matches));
    render(
      <MatchResultsFromMatchPlay
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Fetch Matches/i }));
    await screen.findByText(`Loaded ${matches.length} matches`);
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("orders playoff matches by set number before match number, after qualifications", async () => {
    await renderAndFetch([
      makeMatch("sf2m1", "sf", 2, 1),
      makeMatch("f1m1", "f", 1, 1),
      makeMatch("sf1m2", "sf", 1, 2),
      makeMatch("sf1m1", "sf", 1, 1),
      makeMatch("qm2", "qm", 1, 2),
      makeMatch("qm1", "qm", 1, 1),
    ]);

    const names = screen
      .getAllByRole("row")
      .slice(1)
      .map((row) => row.querySelector("strong")?.textContent);
    expect(names).toEqual([
      "Qualification 1",
      "Qualification 2",
      "Semifinal 1-1",
      "Semifinal 1-2",
      "Semifinal 2-1",
      "Final 1-1",
    ]);
  });

  it("lets the user edit both alliance scores before updating", async () => {
    mockMakeTrustedRequest.mockResolvedValue(makeJsonResponse({}));
    await renderAndFetch([makeMatch("qm1", "qm", 1, 1, { red: 10, blue: 20 })]);
    const [redInput, blueInput] = screen.getAllByPlaceholderText("Score");
    expect(redInput).toHaveValue(10);
    expect(blueInput).toHaveValue(20);

    fireEvent.change(redInput, { target: { value: "55" } });
    fireEvent.change(blueInput, { target: { value: "44" } });
    expect(redInput).toHaveValue(55);
    expect(blueInput).toHaveValue(44);

    fireEvent.click(screen.getByRole("button", { name: /Update/i }));

    await screen.findByText("Successfully updated Qualification 1!");
    const body = JSON.parse(mockMakeTrustedRequest.mock.calls[0][1]);
    expect(body[0].alliances.red.score).toBe(55);
    expect(body[0].alliances.blue.score).toBe(44);
  });

  it("refuses to update a match until both scores are valid numbers", async () => {
    await renderAndFetch([makeMatch("qm1", "qm", 1, 1)]);
    const [redInput] = screen.getAllByPlaceholderText("Score");
    expect(redInput).toHaveValue(null);
    fireEvent.change(redInput, { target: { value: "12" } });

    fireEvent.click(screen.getByRole("button", { name: /Update/i }));

    expect(
      screen.getByText("Please enter valid scores for both alliances")
    ).toBeInTheDocument();
    expect(mockMakeTrustedRequest).not.toHaveBeenCalled();
  });
});
