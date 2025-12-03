/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import MatchVideosTab from "../MatchVideosTab";

describe("MatchVideosTab", () => {
  const mockMakeTrustedRequest = jest.fn();
  const mockMakeApiV3Request = jest.fn();
  const selectedEvent = "2024nytr";

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders the component with correct headings", () => {
      render(
        <MatchVideosTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      expect(screen.getByText("Match Videos")).toBeInTheDocument();
      expect(
        screen.getByText(/Fetch matches from TBA and add YouTube videos/)
      ).toBeInTheDocument();
    });

    it("disables Fetch Matches button when no event is selected", () => {
      render(
        <MatchVideosTab
          selectedEvent=""
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      const btn = screen.getByRole("button", { name: /Fetch Matches/i });
      expect(btn).toBeDisabled();
    });

    it("enables Fetch Matches button when event is selected", () => {
      render(
        <MatchVideosTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      const btn = screen.getByRole("button", { name: /Fetch Matches/i });
      expect(btn).toBeEnabled();
    });
  });

  describe("Fetching Matches", () => {
    it("calls makeApiV3Request when Fetch Matches is clicked", () => {
      render(
        <MatchVideosTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      const btn = screen.getByRole("button", { name: /Fetch Matches/i });
      fireEvent.click(btn);

      expect(mockMakeApiV3Request).toHaveBeenCalledWith(
        `/api/v3/event/${selectedEvent}/matches`,
        expect.any(Function),
        expect.any(Function)
      );
    });

    it("displays matches after successful fetch", async () => {
      const mockMatches = [
        {
          key: "2024nytr_qm1",
          comp_level: "qm",
          set_number: 1,
          match_number: 1,
          alliances: {
            red: { team_keys: ["frc254", "frc971", "frc1678"], score: 100 },
            blue: { team_keys: ["frc1323", "frc2056", "frc5499"], score: 90 },
          },
          videos: [],
        },
        {
          key: "2024nytr_qm2",
          comp_level: "qm",
          set_number: 1,
          match_number: 2,
          alliances: {
            red: { team_keys: ["frc254", "frc971", "frc1678"], score: 110 },
            blue: { team_keys: ["frc1323", "frc2056", "frc5499"], score: 95 },
          },
          videos: [{ type: "youtube", key: "abc123" }],
        },
      ];

      mockMakeApiV3Request.mockImplementation((path, onSuccess) => {
        onSuccess(mockMatches);
      });

      render(
        <MatchVideosTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      const btn = screen.getByRole("button", { name: /Fetch Matches/i });
      fireEvent.click(btn);

      await waitFor(() => {
        expect(screen.getByText("Qualification 1")).toBeInTheDocument();
        expect(screen.getByText("Qualification 2")).toBeInTheDocument();
      });

      // Check that one match shows "No videos" and one shows video ID
      expect(screen.getByText("No videos")).toBeInTheDocument();
      expect(screen.getByText("abc123")).toBeInTheDocument();
    });
  });

  describe("Adding Videos", () => {
    beforeEach(async () => {
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
          videos: [],
        },
      ];

      mockMakeApiV3Request.mockImplementation((path, onSuccess) => {
        onSuccess(mockMatches);
      });

      render(
        <MatchVideosTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      const btn = screen.getByRole("button", { name: /Fetch Matches/i });
      fireEvent.click(btn);

      await waitFor(() => {
        expect(screen.getByText("Qualification 1")).toBeInTheDocument();
      });
    });

    it("adds a video when Add button is clicked", async () => {
      mockMakeTrustedRequest.mockImplementation((path, body, onSuccess) => {
        onSuccess();
      });

      const input = screen.getByPlaceholderText("YouTube ID");
      fireEvent.change(input, { target: { value: "newVideoId123" } });

      const addButton = screen.getByRole("button", { name: /Add/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
          `/api/trusted/v1/event/${selectedEvent}/match_videos/add`,
          JSON.stringify({ qm1: "newVideoId123" }),
          expect.any(Function),
          expect.any(Function)
        );
      });
    });

    it("shows error message when trying to add empty video ID", async () => {
      const addButton = screen.getByRole("button", { name: /Add/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(
          screen.getByText("Please enter a YouTube video ID")
        ).toBeInTheDocument();
      });

      expect(mockMakeTrustedRequest).not.toHaveBeenCalled();
    });

    it("updates state inline after successful video add without refetching", async () => {
      mockMakeTrustedRequest.mockImplementation((path, body, onSuccess) => {
        onSuccess();
      });

      const input = screen.getByPlaceholderText("YouTube ID");
      fireEvent.change(input, { target: { value: "newVideoId123" } });

      const addButton = screen.getByRole("button", { name: /Add/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        // Should only be called once for initial fetch, not again for refresh
        expect(mockMakeApiV3Request).toHaveBeenCalledTimes(1);
        // Video should appear in the UI via state update
        expect(screen.getByText("newVideoId123")).toBeInTheDocument();
      });
    });
  });

  describe("Match Formatting", () => {
    it("formats qualification matches correctly", async () => {
      const mockMatches = [
        {
          key: "2024nytr_qm15",
          comp_level: "qm",
          set_number: 1,
          match_number: 15,
          alliances: { red: { team_keys: [] }, blue: { team_keys: [] } },
          videos: [],
        },
      ];

      mockMakeApiV3Request.mockImplementation((path, onSuccess) => {
        onSuccess(mockMatches);
      });

      render(
        <MatchVideosTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      const btn = screen.getByRole("button", { name: /Fetch Matches/i });
      fireEvent.click(btn);

      await waitFor(() => {
        expect(screen.getByText("Qualification 15")).toBeInTheDocument();
      });
    });

    it("formats playoff matches correctly", async () => {
      const mockMatches = [
        {
          key: "2024nytr_qf2m1",
          comp_level: "qf",
          set_number: 2,
          match_number: 1,
          alliances: { red: { team_keys: [] }, blue: { team_keys: [] } },
          videos: [],
        },
      ];

      mockMakeApiV3Request.mockImplementation((path, onSuccess) => {
        onSuccess(mockMatches);
      });

      render(
        <MatchVideosTab
          selectedEvent={selectedEvent}
          makeTrustedRequest={mockMakeTrustedRequest}
          makeApiV3Request={mockMakeApiV3Request}
        />
      );

      const btn = screen.getByRole("button", { name: /Fetch Matches/i });
      fireEvent.click(btn);

      await waitFor(() => {
        expect(screen.getByText("Quarterfinal 2-1")).toBeInTheDocument();
      });
    });
  });
});
