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

interface Alliance {
  team_keys: string[];
  score?: number;
}

interface SimpleMatch {
  key: string;
  comp_level: string;
  set_number: number;
  match_number: number;
  alliances: {
    red: Alliance;
    blue: Alliance;
  };
}

interface MatchScores {
  red: string;
  blue: string;
}

interface MatchResultsFromMatchPlayProps {
  selectedEvent: string;
  makeTrustedRequest: (
    path: string,
    body: string,
    successCallback: (response: any) => void,
    errorCallback: (error: any) => void
  ) => void;
  makeApiV3Request: <T = unknown>(
    path: string
  ) => Promise<T>;
}

const MatchResultsFromMatchPlay: React.FC<MatchResultsFromMatchPlayProps> = ({
  selectedEvent,
  makeTrustedRequest,
  makeApiV3Request,
}) => {
  const [matches, setMatches] = useState<SimpleMatch[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [scores, setScores] = useState<Record<string, MatchScores>>({});
  const [updatingMatches, setUpdatingMatches] = useState<Record<string, boolean>>({});

  const fetchMatches = async (): Promise<void> => {
    if (!selectedEvent) {
      setStatusMessage("Please select an event first");
      return;
    }

    setLoading(true);
    setStatusMessage("Loading matches...");

    try {
      const data = await makeApiV3Request<SimpleMatch[]>(
        `/api/v3/event/${selectedEvent}/matches/simple`
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

      // Initialize scores from existing match data
      const initialScores: Record<string, MatchScores> = {};
      sortedMatches.forEach((match) => {
        const key = match.key;
        initialScores[key] = {
          red: match.alliances?.red?.score?.toString() ?? "",
          blue: match.alliances?.blue?.score?.toString() ?? "",
        };
      });
      setScores(initialScores);

      setStatusMessage(`Loaded ${sortedMatches.length} matches`);
      setLoading(false);
    } catch (error) {
      setStatusMessage(`Error loading matches: ${error}`);
      setMatches([]);
      setLoading(false);
    }
  };

  const handleScoreChange = (
    matchKey: string,
    alliance: "red" | "blue",
    value: string
  ): void => {
    setScores((prev) => ({
      ...prev,
      [matchKey]: {
        ...prev[matchKey],
        [alliance]: value,
      },
    }));
  };

  const updateMatch = (match: SimpleMatch): void => {
    const matchKey = match.key;
    const redScore = parseInt(scores[matchKey]?.red);
    const blueScore = parseInt(scores[matchKey]?.blue);

    if (isNaN(redScore) || isNaN(blueScore)) {
      setStatusMessage("Please enter valid scores for both alliances");
      return;
    }

    setUpdatingMatches((prev) => ({ ...prev, [matchKey]: true }));
    setStatusMessage(`Updating ${formatMatchName(match)}...`);

    const matchUpdate = {
      comp_level: match.comp_level,
      set_number: match.set_number,
      match_number: match.match_number,
      alliances: {
        red: {
          teams: match.alliances.red.team_keys,
          score: redScore,
        },
        blue: {
          teams: match.alliances.blue.team_keys,
          score: blueScore,
        },
      },
    };

    makeTrustedRequest(
      `/api/trusted/v1/event/${selectedEvent}/matches/update`,
      JSON.stringify([matchUpdate]),
      () => {
        setUpdatingMatches((prev) => ({ ...prev, [matchKey]: false }));
        setStatusMessage(`Successfully updated ${formatMatchName(match)}!`);
      },
      (error) => {
        setUpdatingMatches((prev) => ({ ...prev, [matchKey]: false }));
        setStatusMessage(`Error updating match: ${error}`);
      }
    );
  };

  const formatMatchName = (match: SimpleMatch): string => {
    const levelName = COMP_LEVEL_NAMES[match.comp_level] || match.comp_level;
    if (match.comp_level === "qm") {
      return `${levelName} ${match.match_number}`;
    }
    return `${levelName} ${match.set_number}-${match.match_number}`;
  };

  const formatTeams = (teamKeys: string[]): string => {
    return teamKeys.map((key) => key.replace("frc", "")).join(", ");
  };

  return (
    <div>
      <h4>Manual Match Score Entry</h4>
      <p>
        Fetch matches from TBA and update scores. This lets you manually enter
        match scores for events.
      </p>

      <div className="row">
        <div className="col-sm-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h4 className="panel-title">Match Score Entry</h4>
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
                  <th>Red Alliance</th>
                  <th>Red Score</th>
                  <th>Blue Score</th>
                  <th>Blue Alliance</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {matches.map((match) => (
                  <tr key={match.key}>
                    <td>
                      <strong>{formatMatchName(match)}</strong>
                    </td>
                    <td style={{ color: "#d9534f" }}>
                      {formatTeams(match.alliances.red.team_keys)}
                    </td>
                    <td>
                      <input
                        type="number"
                        className="form-control input-sm"
                        style={{ width: "80px" }}
                        value={scores[match.key]?.red ?? ""}
                        onChange={(e: ChangeEvent<HTMLInputElement>) =>
                          handleScoreChange(match.key, "red", e.target.value)
                        }
                        placeholder="Score"
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        className="form-control input-sm"
                        style={{ width: "80px" }}
                        value={scores[match.key]?.blue ?? ""}
                        onChange={(e: ChangeEvent<HTMLInputElement>) =>
                          handleScoreChange(match.key, "blue", e.target.value)
                        }
                        placeholder="Score"
                      />
                    </td>
                    <td style={{ color: "#5bc0de" }}>
                      {formatTeams(match.alliances.blue.team_keys)}
                    </td>
                    <td>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => updateMatch(match)}
                        disabled={updatingMatches[match.key]}
                      >
                        {updatingMatches[match.key] ? (
                          <span>
                            <span className="glyphicon glyphicon-refresh"></span>{" "}
                            Updating...
                          </span>
                        ) : (
                          <span>
                            <span className="glyphicon glyphicon-upload"></span>{" "}
                            Update
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

export default MatchResultsFromMatchPlay;
