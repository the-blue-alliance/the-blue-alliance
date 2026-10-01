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

  describe("Deleting Videos", () => {
    const mockMatchWithVideo = {
      key: "2024nytr_qm1",
      comp_level: "qm",
      set_number: 1,
      match_number: 1,
      alliances: { red: { team_keys: [] }, blue: { team_keys: [] } },
      videos: [{ type: "youtube", key: "existingVid1" }],
    };

    beforeEach(async () => {
      mockMakeApiV3Request.mockResolvedValue(
        makeApiV3JsonResponse([mockMatchWithVideo])
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
        expect(screen.getByText("existingVid1")).toBeInTheDocument();
      });
    });

    it("shows delete button for each existing video", () => {
      const deleteBtn = screen.getByRole("button", {
        name: /Delete video existingVid1/i,
      });
      expect(deleteBtn).toBeInTheDocument();
      expect(deleteBtn).toBeEnabled();
    });

    it("calls delete endpoint with DELETE method when delete button is clicked", async () => {
      mockMakeTrustedRequest.mockResolvedValue(makeTrustedJsonResponse({}));

      fireEvent.click(
        screen.getByRole("button", { name: /Delete video existingVid1/i })
      );

      await waitFor(() => {
        expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
          `/api/trusted/v1/event/${selectedEvent}/match_videos/delete`,
          JSON.stringify({ qm1: "existingVid1" }),
          "DELETE"
        );
      });
    });

    it("removes video from UI after successful deletion", async () => {
      mockMakeTrustedRequest.mockResolvedValue(makeTrustedJsonResponse({}));

      fireEvent.click(
        screen.getByRole("button", { name: /Delete video existingVid1/i })
      );

      await waitFor(() => {
        expect(screen.queryByText("existingVid1")).not.toBeInTheDocument();
        expect(screen.getByText("No videos")).toBeInTheDocument();
      });
    });

    it("shows success status after deletion", async () => {
      mockMakeTrustedRequest.mockResolvedValue(makeTrustedJsonResponse({}));

      fireEvent.click(
        screen.getByRole("button", { name: /Delete video existingVid1/i })
      );

      await waitFor(() => {
        expect(
          screen.getByText(/Successfully deleted video from Qualification 1/)
        ).toBeInTheDocument();
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

describe("MatchVideosTab playlist parsing, sorting and failure handling", () => {
  const mockMakeTrustedRequest = jest.fn();
  const mockMakeApiV3Request = jest.fn();
  const selectedEvent = "2024nytr";

  const jsonResponse = (payload: unknown): Response =>
    ({ ok: true, json: async () => payload }) as Response;

  const makeMatch = (
    partial: string,
    comp_level: string,
    set_number: number,
    match_number: number,
    videos: Array<{ type: string; key: string }> = []
  ) => ({
    key: `${selectedEvent}_${partial}`,
    comp_level,
    set_number,
    match_number,
    videos,
  });

  const qm1 = makeMatch("qm1", "qm", 1, 1, [{ type: "youtube", key: "vid-qm1" }]);
  const qm2 = makeMatch("qm2", "qm", 1, 2, [{ type: "tba", key: "not-youtube" }]);
  const sf1m1 = makeMatch("sf1m1", "sf", 1, 1);
  const sf2m1 = makeMatch("sf2m1", "sf", 2, 1);

  const renderAndFetch = async (matches: unknown[]): Promise<void> => {
    mockMakeApiV3Request.mockResolvedValue(jsonResponse(matches));
    render(
      <MatchVideosTab
        selectedEvent={selectedEvent}
        makeTrustedRequest={mockMakeTrustedRequest}
        makeApiV3Request={mockMakeApiV3Request}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Fetch Matches/i }));
    await screen.findByText(`Loaded ${matches.length} matches`);
  };

  const rowFor = (matchName: string): HTMLElement =>
    screen.getByText(matchName).closest("tr") as HTMLElement;

  const videoIdInput = (matchName: string): HTMLInputElement =>
    rowFor(matchName).querySelector('input[placeholder="YouTube ID"]') as HTMLInputElement;

  const loadPlaylist = async (input: string): Promise<void> => {
    fireEvent.change(screen.getByPlaceholderText("YouTube playlist URL or ID"), {
      target: { value: input },
    });
    fireEvent.click(screen.getByRole("button", { name: /Load Playlist/i }));
  };

  const status = () => screen.getByText(/Autofilled|Error|Please|Success|Loaded|No new/);

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("orders playoff matches by set then match number and hides non-YouTube videos", async () => {
    await renderAndFetch([sf2m1, qm2, sf1m1, qm1]);

    const names = screen
      .getAllByRole("row")
      .slice(1)
      .map((row) => row.querySelector("strong")?.textContent);
    expect(names).toEqual([
      "Qualification 1",
      "Qualification 2",
      "Semifinal 1-1",
      "Semifinal 2-1",
    ]);
    expect(screen.getByText("vid-qm1")).toHaveAttribute(
      "href",
      "https://www.youtube.com/watch?v=vid-qm1"
    );
    expect(screen.queryByText("not-youtube")).not.toBeInTheDocument();
    expect(rowFor("Qualification 2").querySelectorAll("li")).toHaveLength(0);
    expect(rowFor("Semifinal 1-1")).toHaveTextContent("No videos");
  });

  describe("playlist input parsing", () => {
    it("rejects an empty playlist field", async () => {
      await renderAndFetch([sf1m1]);

      await loadPlaylist("   ");

      expect(
        screen.getByText("Please enter a valid YouTube playlist URL or ID")
      ).toBeInTheDocument();
      expect(mockMakeTrustedRequest).not.toHaveBeenCalled();
    });

    it("accepts a bare playlist ID", async () => {
      mockMakeTrustedRequest.mockResolvedValue(jsonResponse([]));
      await renderAndFetch([sf1m1]);

      await loadPlaylist("PLabc_123-XYZ");

      await waitFor(() => {
        expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
          "/api/_eventwizard/_playlist/2024nytr/PLabc_123-XYZ",
          ""
        );
      });
    });

    it("falls back to regex parsing for inputs that are not valid URLs", async () => {
      mockMakeTrustedRequest.mockResolvedValue(jsonResponse([]));
      await renderAndFetch([sf1m1]);

      await loadPlaylist("watch?v=abc&list=PLfromregex&index=2");

      await waitFor(() => {
        expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
          "/api/_eventwizard/_playlist/2024nytr/PLfromregex",
          ""
        );
      });
    });

    it("rejects a URL that has no list parameter", async () => {
      await renderAndFetch([sf1m1]);

      await loadPlaylist("https://www.youtube.com/watch?v=abc");

      expect(
        screen.getByText("Please enter a valid YouTube playlist URL or ID")
      ).toBeInTheDocument();
      expect(mockMakeTrustedRequest).not.toHaveBeenCalled();
    });
  });

  describe("playlist responses", () => {
    it("reports an unexpected response shape", async () => {
      mockMakeTrustedRequest.mockResolvedValue(jsonResponse({ nope: true }));
      await renderAndFetch([sf1m1]);

      await loadPlaylist("PLabc");

      expect(
        await screen.findByText(
          "Error loading playlist: Error: Unexpected playlist response format"
        )
      ).toBeInTheDocument();
    });

    it("reports request failures", async () => {
      mockMakeTrustedRequest.mockRejectedValue(new Error("boom"));
      await renderAndFetch([sf1m1]);

      await loadPlaylist("PLabc");

      expect(
        await screen.findByText("Error loading playlist: Error: boom")
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Load Playlist/i })).toBeEnabled();
    });

    it("skips unusable entries, existing videos, typed IDs and duplicates", async () => {
      mockMakeTrustedRequest.mockResolvedValue(
        jsonResponse([
          { video_title: "no partial", video_id: "v0" },
          { guessed_match_partial: "qm1", video_title: "no id" },
          { guessed_match_partial: "qm99", video_id: "v-unknown" },
          { guessed_match_partial: "qm1", video_id: "vid-qm1" },
          { guessed_match_partial: "SF2M1", video_id: "v-typed" },
          { guessed_match_partial: "sf1m1", video_id: "v-first", video_title: "SF 1-1 video" },
          { guessed_match_partial: "sf1m1", video_id: "v-second" },
          { guessed_match_partial: "qm2", video_id: "v-untitled" },
        ])
      );
      await renderAndFetch([qm1, qm2, sf1m1, sf2m1]);
      fireEvent.change(videoIdInput("Semifinal 2-1"), {
        target: { value: "already-typed" },
      });

      await loadPlaylist("PLabc");

      expect(
        await screen.findByText(
          "Autofilled 2 match videos from playlist (1 already on matches)"
        )
      ).toBeInTheDocument();
      expect(videoIdInput("Qualification 1")).toHaveValue("");
      expect(videoIdInput("Qualification 2")).toHaveValue("v-untitled");
      expect(videoIdInput("Semifinal 1-1")).toHaveValue("v-first");
      expect(videoIdInput("Semifinal 2-1")).toHaveValue("already-typed");
      expect(screen.getByText("SF 1-1 video")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Add All (3)" })).toBeEnabled();
    });
  });

  describe("playlist titles", () => {
    const autofillWithTitle = async (): Promise<void> => {
      mockMakeTrustedRequest.mockResolvedValueOnce(
        jsonResponse([
          { guessed_match_partial: "sf1m1", video_id: "v-first", video_title: "SF 1-1 video" },
        ])
      );
      await renderAndFetch([sf1m1, sf2m1]);
      await loadPlaylist("PLabc");
      await screen.findByText("SF 1-1 video");
    };

    it("clears the suggested title when the video ID is edited by hand", async () => {
      await autofillWithTitle();

      fireEvent.change(videoIdInput("Semifinal 1-1"), {
        target: { value: "manual" },
      });

      expect(screen.queryByText("SF 1-1 video")).not.toBeInTheDocument();
      expect(videoIdInput("Semifinal 1-1")).toHaveValue("manual");
    });

    it("clears the suggested title once the video has been added", async () => {
      await autofillWithTitle();
      mockMakeTrustedRequest.mockResolvedValueOnce(jsonResponse({}));

      fireEvent.click(
        rowFor("Semifinal 1-1").querySelector("button.btn-primary") as HTMLElement
      );

      expect(
        await screen.findByText("Successfully added video to Semifinal 1-1!")
      ).toBeInTheDocument();
      expect(screen.queryByText("SF 1-1 video")).not.toBeInTheDocument();
      expect(screen.getByText("v-first")).toBeInTheDocument();
      expect(rowFor("Semifinal 2-1")).toHaveTextContent("No videos");
    });
  });

  describe("failed mutations", () => {
    it("reports a failed single add and re-enables the row", async () => {
      mockMakeTrustedRequest.mockRejectedValue(new Error("boom"));
      await renderAndFetch([sf1m1]);
      fireEvent.change(videoIdInput("Semifinal 1-1"), {
        target: { value: "new-vid" },
      });

      fireEvent.click(
        rowFor("Semifinal 1-1").querySelector("button.btn-primary") as HTMLElement
      );

      expect(
        await screen.findByText("Error adding video: Error: boom")
      ).toBeInTheDocument();
      expect(rowFor("Semifinal 1-1").querySelector("button.btn-primary")).toBeEnabled();
      expect(videoIdInput("Semifinal 1-1")).toHaveValue("new-vid");
    });

    it("reports a failed Add All and keeps the pending IDs", async () => {
      mockMakeTrustedRequest.mockRejectedValue(new Error("boom"));
      await renderAndFetch([sf1m1, sf2m1]);
      fireEvent.change(videoIdInput("Semifinal 1-1"), {
        target: { value: "new-vid" },
      });

      fireEvent.click(screen.getByRole("button", { name: "Add All (1)" }));

      expect(
        await screen.findByText("Error adding videos: Error: boom")
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Add All (1)" })).toBeEnabled();
      expect(videoIdInput("Semifinal 1-1")).toHaveValue("new-vid");
    });

    it("reports a failed delete and keeps the video", async () => {
      mockMakeTrustedRequest.mockRejectedValue(new Error("boom"));
      await renderAndFetch([qm1, sf1m1]);

      fireEvent.click(screen.getByRole("button", { name: "Delete video vid-qm1" }));

      expect(
        await screen.findByText("Error deleting video: Error: boom")
      ).toBeInTheDocument();
      expect(screen.getByText("vid-qm1")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Delete video vid-qm1" })).toBeEnabled();
    });
  });

  it("adds all pending videos while leaving other matches untouched", async () => {
    mockMakeTrustedRequest.mockResolvedValue(jsonResponse({}));
    await renderAndFetch([qm1, sf1m1, sf2m1]);
    fireEvent.change(videoIdInput("Semifinal 1-1"), {
      target: { value: "  new-vid  " },
    });

    fireEvent.click(screen.getByRole("button", { name: "Add All (1)" }));

    expect(
      await screen.findByText("Successfully added 1 videos!")
    ).toBeInTheDocument();
    expect(mockMakeTrustedRequest).toHaveBeenCalledWith(
      "/api/trusted/v1/event/2024nytr/match_videos/add",
      JSON.stringify({ sf1m1: "new-vid" })
    );
    expect(screen.getByText("new-vid")).toBeInTheDocument();
    expect(videoIdInput("Semifinal 1-1")).toHaveValue("");
    expect(rowFor("Semifinal 2-1")).toHaveTextContent("No videos");
    expect(screen.getByText("vid-qm1")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add All" })).toBeDisabled();
  });

  it("deletes a video from one match without touching the others", async () => {
    mockMakeTrustedRequest.mockResolvedValue(jsonResponse({}));
    await renderAndFetch([
      qm1,
      makeMatch("qm3", "qm", 1, 3, [{ type: "youtube", key: "vid-qm3" }]),
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Delete video vid-qm1" }));

    expect(
      await screen.findByText("Successfully deleted video from Qualification 1!")
    ).toBeInTheDocument();
    expect(screen.queryByText("vid-qm1")).not.toBeInTheDocument();
    expect(screen.getByText("vid-qm3")).toBeInTheDocument();
  });
});
