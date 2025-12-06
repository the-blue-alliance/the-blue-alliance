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

export interface MatchVideosTabProps {
  selectedEvent: string;
  makeTrustedRequest: (
    path: string,
    body: string
  ) => Promise<Response>;
  makeApiV3Request: <T = unknown>(
    path: string
  ) => Promise<T>;
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

  const fetchMatches = async (): Promise<void> => {
    if (!selectedEvent) {
      setStatusMessage("Please select an event first");
      return;
    }

    setLoading(true);
    setStatusMessage("Loading matches...");

    try {
      const data = await makeApiV3Request<Match[]>(
        `/api/v3/event/${selectedEvent}/matches`
      );

      // Sort matches by comp_level and match_number
      const sortedMatches = data.sort((a, b) => {
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
      setLoading(false);
    } catch (error) {
      setStatusMessage(`Error loading matches: ${error}`);
      setMatches([]);
      setLoading(false);
    }
  };

  const handleVideoIdChange = (matchKey: string, value: string): void => {
    setNewVideoIds((prev) => ({
      ...prev,
      [matchKey]: value,
    }));
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
