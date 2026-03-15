import React, { ChangeEvent, useState } from "react";

const COMP_LEVELS_PLAY_ORDER: Record<string, number> = {
  qm: 1,
  ef: 2,
  qf: 3,
  sf: 4,
  f: 5,
};

const COMP_LEVEL_NAMES: Record<string, string> = {
  qm: "Qualification",
  ef: "Octofinal",
  qf: "Quarterfinal",
  sf: "Semifinal",
  f: "Final",
};

interface Video {
  type: string;
  key: string;
}

interface Match {
  key: string;
  comp_level: string;
  set_number: number;
  match_number: number;
  videos: Video[];
}

interface PlaylistVideo {
  video_title: string;
  video_id: string;
  guessed_match_partial: string;
}

export interface MatchVideosTabProps {
  selectedEvent: string;
  makeTrustedRequest: (
    path: string,
    body: string
  ) => Promise<Response>;
  makeApiV3Request: (
    path: string
  ) => Promise<Response>;
}

const MatchVideosTab: React.FC<MatchVideosTabProps> = ({
  selectedEvent,
  makeTrustedRequest,
  makeApiV3Request,
}) => {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [newVideoIds, setNewVideoIds] = useState<Record<string, string>>({});
  const [addingVideos, setAddingVideos] = useState<Record<string, boolean>>({});
  const [playlistUrl, setPlaylistUrl] = useState<string>("");
  const [loadingPlaylist, setLoadingPlaylist] = useState<boolean>(false);
  const [playlistVideoTitles, setPlaylistVideoTitles] = useState<
    Record<string, string>
  >({});
  const [addingAllVideos, setAddingAllVideos] = useState<boolean>(false);

  const isVideoAlreadyOnMatch = (match: Match, videoId: string): boolean =>
    match.videos?.some((video) => video.type === "youtube" && video.key === videoId) ||
    false;

  const extractPlaylistId = (playlistInput: string): string | null => {
    const trimmed = playlistInput.trim();
    if (!trimmed) {
      return null;
    }

    if (/^[A-Za-z0-9_-]+$/.test(trimmed) && !trimmed.includes("http")) {
      return trimmed;
    }

    try {
      const parsedUrl = new URL(trimmed);
      const playlistId = parsedUrl.searchParams.get("list");
      if (playlistId) {
        return playlistId;
      }
    } catch (_error) {
      // Fall through to regex parsing for non-standard URLs.
    }

    const listMatch = trimmed.match(/[?&]list=([A-Za-z0-9_-]+)/);
    return listMatch ? listMatch[1] : null;
  };

  const getPendingVideoAddPayload = (): Record<string, string> => {
    const payload: Record<string, string> = {};

    matches.forEach((match) => {
      const videoId = newVideoIds[match.key]?.trim();
      if (!videoId || isVideoAlreadyOnMatch(match, videoId)) {
        return;
      }

      const partialMatchKey = match.key.replace(`${selectedEvent}_`, "");
      payload[partialMatchKey] = videoId;
    });

    return payload;
  };

  const fetchMatches = async (): Promise<void> => {
    if (!selectedEvent) {
      setStatusMessage("Please select an event first");
      return;
    }

    setLoading(true);
    setStatusMessage("Loading matches...");

    try {
      const response = await makeApiV3Request(
        `/api/v3/event/${selectedEvent}/matches`
      );
      const data = await response.json();

      if (!Array.isArray(data)) {
        throw new Error("Unexpected matches response format");
      }

      const matchesFromApi = data as Match[];

      // Sort matches by comp_level and match_number
      const sortedMatches = [...matchesFromApi].sort((a, b) => {
        const compLevelDiff =
          COMP_LEVELS_PLAY_ORDER[a.comp_level] -
          COMP_LEVELS_PLAY_ORDER[b.comp_level];
        if (compLevelDiff !== 0) return compLevelDiff;

        // For playoff matches, sort by set_number then match_number
        if (a.comp_level !== "qm") {
          const setDiff = a.set_number - b.set_number;
          if (setDiff !== 0) return setDiff;
        }

        return a.match_number - b.match_number;
      });

      setMatches(sortedMatches);
      setStatusMessage(`Loaded ${sortedMatches.length} matches`);
    } catch (error) {
      setStatusMessage(`Error loading matches: ${error}`);
      setMatches([]);
    } finally {
      setLoading(false);
    }
  };

  const handleVideoIdChange = (matchKey: string, value: string): void => {
    setNewVideoIds((prev) => ({
      ...prev,
      [matchKey]: value,
    }));

    setPlaylistVideoTitles((prev) => {
      if (!prev[matchKey]) {
        return prev;
      }
      const next = { ...prev };
      delete next[matchKey];
      return next;
    });
  };

  const fetchPlaylistVideos = async (): Promise<void> => {
    if (!selectedEvent) {
      setStatusMessage("Please select an event first");
      return;
    }

    if (matches.length === 0) {
      setStatusMessage("Fetch matches before loading a playlist");
      return;
    }

    const playlistId = extractPlaylistId(playlistUrl);
    if (!playlistId) {
      setStatusMessage("Please enter a valid YouTube playlist URL or ID");
      return;
    }

    setLoadingPlaylist(true);
    setStatusMessage("Loading playlist videos...");

    try {
      const response = await makeTrustedRequest(
        `/api/_eventwizard/_playlist/${selectedEvent}/${encodeURIComponent(
          playlistId
        )}`,
        ""
      );
      const data = await response.json();

      if (!Array.isArray(data)) {
        throw new Error("Unexpected playlist response format");
      }

      const matchesByPartial = new Map<string, Match>(
        matches.map((match) => [
          match.key.replace(`${selectedEvent}_`, ""),
          match,
        ])
      );

      const nextVideoIds: Record<string, string> = {};
      const nextVideoTitles: Record<string, string> = {};
      let autofilledCount = 0;
      let skippedExistingCount = 0;

      data.forEach((playlistVideo) => {
        const video = playlistVideo as Partial<PlaylistVideo>;
        const matchPartial = video.guessed_match_partial?.trim().toLowerCase();
        const videoId = video.video_id?.trim();

        if (!matchPartial || !videoId) {
          return;
        }

        const match = matchesByPartial.get(matchPartial);
        if (!match) {
          return;
        }

        if (isVideoAlreadyOnMatch(match, videoId)) {
          skippedExistingCount += 1;
          return;
        }

        if (newVideoIds[match.key]?.trim() || nextVideoIds[match.key]) {
          return;
        }

        nextVideoIds[match.key] = videoId;
        if (video.video_title) {
          nextVideoTitles[match.key] = video.video_title;
        }
        autofilledCount += 1;
      });

      setNewVideoIds((prev) => ({ ...prev, ...nextVideoIds }));
      setPlaylistVideoTitles(nextVideoTitles);

      let status = `Autofilled ${autofilledCount} match videos from playlist`;
      if (skippedExistingCount > 0) {
        status += ` (${skippedExistingCount} already on matches)`;
      }
      setStatusMessage(status);
    } catch (error) {
      setStatusMessage(`Error loading playlist: ${error}`);
    } finally {
      setLoadingPlaylist(false);
    }
  };

  const addAllVideos = async (): Promise<void> => {
    if (!selectedEvent) {
      setStatusMessage("Please select an event first");
      return;
    }

    const payload = getPendingVideoAddPayload();
    const pendingEntries = Object.entries(payload);

    if (pendingEntries.length === 0) {
      setStatusMessage("No new videos to add");
      return;
    }

    setAddingAllVideos(true);
    setStatusMessage(`Adding ${pendingEntries.length} videos...`);

    try {
      await makeTrustedRequest(
        `/api/trusted/v1/event/${selectedEvent}/match_videos/add`,
        JSON.stringify(payload)
      );

      setMatches((prevMatches) =>
        prevMatches.map((match) => {
          const partialMatchKey = match.key.replace(`${selectedEvent}_`, "");
          const videoId = payload[partialMatchKey];
          if (!videoId || isVideoAlreadyOnMatch(match, videoId)) {
            return match;
          }

          return {
            ...match,
            videos: [...match.videos, { type: "youtube", key: videoId }],
          };
        })
      );

      setNewVideoIds((prev) => {
        const next = { ...prev };
        pendingEntries.forEach(([partialMatchKey]) => {
          next[`${selectedEvent}_${partialMatchKey}`] = "";
        });
        return next;
      });

      setPlaylistVideoTitles((prev) => {
        const next = { ...prev };
        pendingEntries.forEach(([partialMatchKey]) => {
          delete next[`${selectedEvent}_${partialMatchKey}`];
        });
        return next;
      });

      setStatusMessage(`Successfully added ${pendingEntries.length} videos!`);
    } catch (error) {
      setStatusMessage(`Error adding videos: ${error}`);
    } finally {
      setAddingAllVideos(false);
    }
  };

  const addVideo = async (match: Match): Promise<void> => {
    const matchKey = match.key;
    const videoId = newVideoIds[matchKey]?.trim();

    if (!videoId) {
      setStatusMessage("Please enter a YouTube video ID");
      return;
    }

    setAddingVideos((prev) => ({ ...prev, [matchKey]: true }));
    setStatusMessage(`Adding video to ${formatMatchName(match)}...`);

    // The API expects a dict of partial match key to video ID
    // Partial match key is just the comp_level + match/set numbers (without event key)
    const partialMatchKey = matchKey.replace(`${selectedEvent}_`, "");

    try {
      await makeTrustedRequest(
        `/api/trusted/v1/event/${selectedEvent}/match_videos/add`,
        JSON.stringify({ [partialMatchKey]: videoId })
      );
      setAddingVideos((prev) => ({ ...prev, [matchKey]: false }));
      setStatusMessage(
        `Successfully added video to ${formatMatchName(match)}!`
      );
      // Clear the input
      setNewVideoIds((prev) => ({ ...prev, [matchKey]: "" }));
      setPlaylistVideoTitles((prev) => {
        if (!prev[matchKey]) {
          return prev;
        }
        const next = { ...prev };
        delete next[matchKey];
        return next;
      });
      // Update state inline instead of refetching to avoid server data lag
      setMatches((prevMatches) =>
        prevMatches.map((m) => {
          if (m.key === matchKey) {
            return {
              ...m,
              videos: [...m.videos, { type: "youtube", key: videoId }],
            };
          }
          return m;
        })
      );
    } catch (error) {
      setAddingVideos((prev) => ({ ...prev, [matchKey]: false }));
      setStatusMessage(`Error adding video: ${error}`);
    }
  };

  const formatMatchName = (match: Match): string => {
    const levelName = COMP_LEVEL_NAMES[match.comp_level] || match.comp_level;
    if (match.comp_level === "qm") {
      return `${levelName} ${match.match_number}`;
    }
    return `${levelName} ${match.set_number}-${match.match_number}`;
  };

  const extractVideoId = (video: Video): string | null => {
    // Extract just the video ID from the video object
    if (video.type === "youtube") {
      return video.key;
    }
    return null;
  };

  const pendingAddCount = Object.keys(getPendingVideoAddPayload()).length;

  return (
    <div className="tab-pane" id="match-videos">
      <h3>Match Videos</h3>
      <p>
        Fetch matches from TBA and add YouTube videos to them. Videos will be
        visible on match pages and in the event video gallery.
      </p>

      <div className="row">
        <div className="col-sm-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h4 className="panel-title">Manage Match Videos</h4>
            </div>
            <div className="panel-body">
              <button
                className="btn btn-primary"
                onClick={fetchMatches}
                disabled={loading || !selectedEvent}
              >
                {loading ? "Loading..." : "Fetch Matches"}
              </button>

              <div className="form-inline" style={{ marginTop: "15px" }}>
                <div
                  className="form-group"
                  style={{ minWidth: "350px", marginRight: "10px" }}
                >
                  <input
                    type="text"
                    className="form-control"
                    placeholder="YouTube playlist URL or ID"
                    value={playlistUrl}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      setPlaylistUrl(e.target.value)
                    }
                    disabled={!selectedEvent || loadingPlaylist || addingAllVideos}
                    style={{ width: "100%" }}
                  />
                </div>
                <button
                  className="btn btn-default"
                  onClick={fetchPlaylistVideos}
                  disabled={
                    !selectedEvent ||
                    loadingPlaylist ||
                    addingAllVideos ||
                    matches.length === 0
                  }
                  style={{ marginRight: "10px" }}
                >
                  {loadingPlaylist ? "Loading Playlist..." : "Load Playlist"}
                </button>
                <button
                  className="btn btn-success"
                  onClick={addAllVideos}
                  disabled={
                    !selectedEvent ||
                    addingAllVideos ||
                    loadingPlaylist ||
                    pendingAddCount === 0
                  }
                >
                  {addingAllVideos
                    ? "Adding All..."
                    : `Add All${pendingAddCount > 0 ? ` (${pendingAddCount})` : ""}`}
                </button>
              </div>

              {statusMessage && (
                <div className="alert alert-info" style={{ marginTop: "15px" }}>
                  {statusMessage}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {matches.length > 0 && (
        <div className="row" style={{ marginTop: "20px" }}>
          <div className="col-sm-12">
            <table className="table table-striped table-condensed">
              <thead>
                <tr>
                  <th>Match</th>
                  <th>Current Videos</th>
                  <th>Add Video</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {matches.map((match) => (
                  <tr key={match.key}>
                    <td>
                      <strong>{formatMatchName(match)}</strong>
                    </td>
                    <td>
                      {match.videos && match.videos.length > 0 ? (
                        <ul style={{ margin: 0, paddingLeft: "20px" }}>
                          {match.videos.map((video, idx) => {
                            const videoId = extractVideoId(video);
                            return videoId ? (
                              <li key={idx}>
                                <a
                                  href={`https://www.youtube.com/watch?v=${videoId}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  {videoId}
                                </a>
                              </li>
                            ) : null;
                          })}
                        </ul>
                      ) : (
                        <span className="text-muted">No videos</span>
                      )}
                    </td>
                    <td>
                      <input
                        type="text"
                        className="form-control input-sm"
                        style={{ minWidth: "150px" }}
                        value={newVideoIds[match.key] || ""}
                        onChange={(e: ChangeEvent<HTMLInputElement>) =>
                          handleVideoIdChange(match.key, e.target.value)
                        }
                        placeholder="YouTube ID"
                      />
                      {playlistVideoTitles[match.key] && (
                        <small
                          className="text-muted"
                          style={{ display: "block", marginTop: "5px" }}
                        >
                          {playlistVideoTitles[match.key]}
                        </small>
                      )}
                    </td>
                    <td>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => addVideo(match)}
                        disabled={addingVideos[match.key]}
                      >
                        {addingVideos[match.key] ? (
                          <span>
                            <span className="glyphicon glyphicon-refresh"></span>{" "}
                            Adding...
                          </span>
                        ) : (
                          <span>
                            <span className="glyphicon glyphicon-plus"></span>{" "}
                            Add
                          </span>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default MatchVideosTab;
