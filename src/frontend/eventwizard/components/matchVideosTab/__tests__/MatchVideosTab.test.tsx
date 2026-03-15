/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import MatchVideosTab from "../MatchVideosTab";

describe("MatchVideosTab", () => {
  const mockMakeTrustedRequest = jest.fn();
  const mockMakeApiV3Request = jest.fn<Promise<Response>, [string]>();
  const selectedEvent = "2024nytr";

  const makeApiV3JsonResponse = (payload: unknown): Response =>
    ({
      ok: true,
      json: async () => payload,
    } as Response);

  const makeTrustedJsonResponse = (payload: unknown): Response =>
    ({
      ok: true,
      json: async () => payload,
    } as Response);

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
    it("calls makeApiV3Request when Fetch Matches is clicked", async () => {
      mockMakeApiV3Request.mockResolvedValue(makeApiV3JsonResponse([]));
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
        expect(mockMakeApiV3Request).toHaveBeenCalledWith(
          `/api/v3/event/${selectedEvent}/matches`
        );
      });
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

      mockMakeApiV3Request.mockResolvedValue(
        makeApiV3JsonResponse(mockMatches)
      );

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

    it("shows an error when matches response is not an array", async () => {
      mockMakeApiV3Request.mockResolvedValue(
        makeApiV3JsonResponse({ matches: [] })
      );

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
        expect(screen.getByText(/Error loading matches:/)).toBeInTheDocument();
        expect(
          screen.getByText(/Unexpected matches response format/)
        ).toBeInTheDocument();
      });
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

      mockMakeApiV3Request.mockResolvedValue(
        makeApiV3JsonResponse(mockMatches)
      );

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
      mockMakeTrustedRequest.mockResolvedValue(makeTrustedJsonResponse({}));

      const input = screen.getByPlaceholderText("YouTube ID");
      fireEvent.change(input, { target: { value: "newVideoId123" } });

      const addButton = screen.getByRole("button", { name: /^Add$/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
          `/api/trusted/v1/event/${selectedEvent}/match_videos/add`,
          JSON.stringify({ qm1: "newVideoId123" })
        );
      });
    });

    it("shows error message when trying to add empty video ID", async () => {
      const addButton = screen.getByRole("button", { name: /^Add$/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        expect(
          screen.getByText("Please enter a YouTube video ID")
        ).toBeInTheDocument();
      });

      expect(mockMakeTrustedRequest).not.toHaveBeenCalled();
    });

    it("updates state inline after successful video add without refetching", async () => {
      mockMakeTrustedRequest.mockResolvedValue(makeTrustedJsonResponse({}));

      const input = screen.getByPlaceholderText("YouTube ID");
      fireEvent.change(input, { target: { value: "newVideoId123" } });

      const addButton = screen.getByRole("button", { name: /^Add$/i });
      fireEvent.click(addButton);

      await waitFor(() => {
        // Should only be called once for initial fetch, not again for refresh
        expect(mockMakeApiV3Request).toHaveBeenCalledTimes(1);
        // Video should appear in the UI via state update
        expect(screen.getByText("newVideoId123")).toBeInTheDocument();
      });
    });
  });

  describe("Playlist Autofill", () => {
    it("autofills video IDs from playlist by guessed match partial", async () => {
      const mockMatches = [
        {
          key: "2024nytr_qm1",
          comp_level: "qm",
          set_number: 1,
          match_number: 1,
          alliances: { red: { team_keys: [] }, blue: { team_keys: [] } },
          videos: [],
        },
        {
          key: "2024nytr_qm2",
          comp_level: "qm",
          set_number: 1,
          match_number: 2,
          alliances: { red: { team_keys: [] }, blue: { team_keys: [] } },
          videos: [{ type: "youtube", key: "alreadyThere" }],
        },
      ];

      mockMakeApiV3Request.mockResolvedValue(makeApiV3JsonResponse(mockMatches));
      mockMakeTrustedRequest.mockResolvedValue(
        makeTrustedJsonResponse([
          {
            video_title: "Qualification Match 1",
            video_id: "newQm1Video",
            guessed_match_partial: "qm1",
          },
          {
            video_title: "Qualification Match 2",
            video_id: "alreadyThere",
            guessed_match_partial: "qm2",
          },
        ])
      );

      render(
        <MatchVideosTab
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

      fireEvent.change(
        screen.getByPlaceholderText("YouTube playlist URL or ID"),
        {
          target: {
            value: "https://www.youtube.com/playlist?list=PL_TEST_123",
          },
        }
      );
      fireEvent.click(screen.getByRole("button", { name: /Load Playlist/i }));

      await waitFor(() => {
        expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
          `/api/_eventwizard/_playlist/${selectedEvent}/PL_TEST_123`,
          ""
        );
      });

      await waitFor(() => {
        const videoInputs = screen.getAllByPlaceholderText("YouTube ID");
        expect((videoInputs[0] as HTMLInputElement).value).toBe("newQm1Video");
        expect((videoInputs[1] as HTMLInputElement).value).toBe("");
        expect(screen.getByText("Qualification Match 1")).toBeInTheDocument();
      });
    });

    it("adds all pending videos with Add All", async () => {
      const mockMatches = [
        {
          key: "2024nytr_qm1",
          comp_level: "qm",
          set_number: 1,
          match_number: 1,
          alliances: { red: { team_keys: [] }, blue: { team_keys: [] } },
          videos: [],
        },
        {
          key: "2024nytr_qm2",
          comp_level: "qm",
          set_number: 1,
          match_number: 2,
          alliances: { red: { team_keys: [] }, blue: { team_keys: [] } },
          videos: [],
        },
      ];

      mockMakeApiV3Request.mockResolvedValue(makeApiV3JsonResponse(mockMatches));
      mockMakeTrustedRequest.mockResolvedValue(makeTrustedJsonResponse({}));

      render(
        <MatchVideosTab
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

      const videoInputs = screen.getAllByPlaceholderText("YouTube ID");
      fireEvent.change(videoInputs[0], { target: { value: "videoA" } });
      fireEvent.change(videoInputs[1], { target: { value: "videoB" } });

      fireEvent.click(screen.getByRole("button", { name: /Add All \(2\)/i }));

      await waitFor(() => {
        expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
          `/api/trusted/v1/event/${selectedEvent}/match_videos/add`,
          JSON.stringify({ qm1: "videoA", qm2: "videoB" })
        );
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

      mockMakeApiV3Request.mockResolvedValue(
        makeApiV3JsonResponse(mockMatches)
      );

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

      mockMakeApiV3Request.mockResolvedValue(
        makeApiV3JsonResponse(mockMatches)
      );

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
