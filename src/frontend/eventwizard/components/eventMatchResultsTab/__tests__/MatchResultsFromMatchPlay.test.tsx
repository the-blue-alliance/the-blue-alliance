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
