import React, { useState, ChangeEvent } from "react";
import { parseScheduleFile } from "../../utils/scheduleParser";
import { ScheduleMatch } from "../../utils/scheduleParser";

export interface EventScheduleTabProps {
  selectedEvent: string;
  makeTrustedRequest: (
    path: string,
    body: string
  ) => Promise<Response>;
}

const EventScheduleTab: React.FC<EventScheduleTabProps> = ({
  selectedEvent,
  makeTrustedRequest,
}) => {
  const [matches, setMatches] = useState<ScheduleMatch[]>([]);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [file, setFile] = useState<File | null>(null);
  const [compLevelFilter, setCompLevelFilter] = useState<string>("all");
  const [hasOcto, setHasOcto] = useState<boolean>(false);
  const [isDoubleElim, setIsDoubleElim] = useState<boolean>(false);

  const cleanTeamNum = (teamNum: string): string => {
    return teamNum.replace(/^0+/, "") || "0";
  };

  const handleFileChange = async (
    e: ChangeEvent<HTMLInputElement>
  ): Promise<void> => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setLoading(true);
    setStatusMessage("Parsing schedule file...");

    try {
      const parsedMatches = await parseScheduleFile(
        selectedFile,
        selectedEvent,
        compLevelFilter,
        hasOcto,
        isDoubleElim
      );
      setMatches(parsedMatches);
      if (parsedMatches.length > 0) {
        setStatusMessage(`Loaded ${parsedMatches.length} matches`);
      } else {
        setStatusMessage("No matches found with current settings.");
      }
    } catch (error: any) {
      setStatusMessage(`Error parsing file: ${error.message}`);
      setMatches([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = async (
    e: ChangeEvent<HTMLInputElement>
  ): Promise<void> => {
    const newFilter = e.target.value;
    setCompLevelFilter(newFilter);

    if (file) {
      setLoading(true);
      setStatusMessage("Re-parsing with new filter...");
      try {
        const parsedMatches = await parseScheduleFile(
          file,
          selectedEvent,
          newFilter,
          hasOcto,
          isDoubleElim
        );
        setMatches(parsedMatches);
        if (parsedMatches.length > 0) {
          setStatusMessage(`Loaded ${parsedMatches.length} matches`);
        } else {
          setStatusMessage("No matches found with current settings.");
        }
      } catch (error: any) {
        setStatusMessage(`Error parsing file: ${error.message}`);
        setMatches([]);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleAllianceCountChange = async (
    e: ChangeEvent<HTMLInputElement>
  ): Promise<void> => {
    const newHasOcto = e.target.value === "16";
    setHasOcto(newHasOcto);

    if (file) {
      setLoading(true);
      setStatusMessage("Re-parsing with new alliance count...");
      try {
        const parsedMatches = await parseScheduleFile(
          file,
          selectedEvent,
          compLevelFilter,
          newHasOcto,
          isDoubleElim
        );
        setMatches(parsedMatches);
        if (parsedMatches.length > 0) {
          setStatusMessage(`Loaded ${parsedMatches.length} matches`);
        } else {
          setStatusMessage("No matches found with current settings.");
        }
      } catch (error: any) {
        setStatusMessage(`Error parsing file: ${error.message}`);
        setMatches([]);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleSubmit = async (): Promise<void> => {
    if (matches.length === 0) {
      alert("No matches to upload!");
      return;
    }

    setUploading(true);
    setStatusMessage("Uploading matches to TBA...");

    const matchData = matches.map((match) => ({
      comp_level: match.comp_level,
      set_number: match.set_number,
      match_number: match.match_number,
      alliances: match.alliances,
      time: match.time_string,
    }));

    try {
      await makeTrustedRequest(
        `event/${selectedEvent}/matches/update`,
        JSON.stringify(matchData)
      );
      setUploading(false);
      setStatusMessage(
        `Successfully uploaded ${matches.length} matches to TBA!`
      );
      setTimeout(() => {
        setStatusMessage("");
        setMatches([]);
        setFile(null);
        const fileInput = document.getElementById(
          "schedule_file"
        ) as HTMLInputElement;
        if (fileInput) {
          fileInput.value = "";
        }
      }, 3000);
    } catch (error) {
      setUploading(false);
      setStatusMessage(`Error uploading matches: ${error}`);
    }
  };

  return (
    <div className="tab-pane" id="schedule">
      <h3>FMS Schedule Import</h3>

      <div className="row">
        <div className="col-sm-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h4 className="panel-title">Upload FMS Schedule Report</h4>
            </div>
            <div className="panel-body">
              <div className="form-group">
                <label htmlFor="schedule_file">FMS Schedule Excel File</label>
                <input
                  type="file"
                  id="schedule_file"
                  className="form-control"
                  accept=".xls,.xlsx"
                  onChange={handleFileChange}
                  disabled={!selectedEvent || loading || uploading}
                />
              </div>

              <div className="form-group">
                <label>Competition Level Filter</label>
                <div>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="import-comp-level"
                      value="all"
                      checked={compLevelFilter === "all"}
                      onChange={handleFilterChange}
                      disabled={loading || uploading}
                    />
                    All
                  </label>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="import-comp-level"
                      value="qm"
                      checked={compLevelFilter === "qm"}
                      onChange={handleFilterChange}
                      disabled={loading || uploading}
                    />
                    Qualifications
                  </label>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="import-comp-level"
                      value="ef"
                      checked={compLevelFilter === "ef"}
                      onChange={handleFilterChange}
                      disabled={loading || uploading}
                    />
                    Octofinals
                  </label>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="import-comp-level"
                      value="qf"
                      checked={compLevelFilter === "qf"}
                      onChange={handleFilterChange}
                      disabled={loading || uploading}
                    />
                    Quarterfinals
                  </label>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="import-comp-level"
                      value="sf"
                      checked={compLevelFilter === "sf"}
                      onChange={handleFilterChange}
                      disabled={loading || uploading}
                    />
                    Semifinals
                  </label>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="import-comp-level"
                      value="f"
                      checked={compLevelFilter === "f"}
                      onChange={handleFilterChange}
                      disabled={loading || uploading}
                    />
                    Finals
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label>Playoff Format</label>
                <div>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="playoff-format"
                      value="standard"
                      checked={!isDoubleElim}
                      onChange={async () => {
                        setIsDoubleElim(false);
                        if (file) {
                          setLoading(true);
                          setStatusMessage(
                            "Re-parsing with new playoff format..."
                          );
                          try {
                            const parsedMatches = await parseScheduleFile(
                              file,
                              selectedEvent,
                              compLevelFilter,
                              hasOcto,
                              false
                            );
                            setMatches(parsedMatches);
                            if (parsedMatches.length > 0) {
                              setStatusMessage(
                                `Loaded ${parsedMatches.length} matches`
                              );
                            } else {
                              setStatusMessage(
                                "No matches found with current settings."
                              );
                            }
                          } catch (error: any) {
                            setStatusMessage(
                              `Error parsing file: ${error.message}`
                            );
                            setMatches([]);
                          } finally {
                            setLoading(false);
                          }
                        }
                      }}
                      disabled={loading || uploading}
                    />
                    Standard Bracket
                  </label>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="playoff-format"
                      value="doubleelim"
                      checked={isDoubleElim}
                      onChange={async () => {
                        setIsDoubleElim(true);
                        if (file) {
                          setLoading(true);
                          setStatusMessage(
                            "Re-parsing with new playoff format..."
                          );
                          try {
                            const parsedMatches = await parseScheduleFile(
                              file,
                              selectedEvent,
                              compLevelFilter,
                              hasOcto,
                              true
                            );
                            setMatches(parsedMatches);
                            if (parsedMatches.length > 0) {
                              setStatusMessage(
                                `Loaded ${parsedMatches.length} matches`
                              );
                            } else {
                              setStatusMessage(
                                "No matches found with current settings."
                              );
                            }
                          } catch (error: any) {
                            setStatusMessage(
                              `Error parsing file: ${error.message}`
                            );
                            setMatches([]);
                          } finally {
                            setLoading(false);
                          }
                        }
                      }}
                      disabled={loading || uploading}
                    />
                    Double Elimination
                  </label>
                </div>
              </div>

              <div className="form-group">
                <label>
                  Number of Playoff Alliances (Standard Bracket Only)
                </label>
                <div>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="alliance-count-schedule"
                      value="8"
                      checked={!hasOcto}
                      onChange={handleAllianceCountChange}
                      disabled={loading || uploading || isDoubleElim}
                    />
                    8 Alliances
                  </label>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="alliance-count-schedule"
                      value="16"
                      checked={hasOcto}
                      onChange={handleAllianceCountChange}
                      disabled={loading || uploading || isDoubleElim}
                    />
                    16 Alliances
                  </label>
                </div>
              </div>

              {statusMessage && (
                <div className="alert alert-info">{statusMessage}</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {matches.length > 0 && (
        <div className="row">
          <div className="col-sm-12">
            <div className="panel panel-default">
              <div className="panel-heading">
                <h4 className="panel-title">Match Preview</h4>
              </div>
              <div className="panel-body">
                <div className="table-responsive">
                  <table className="table table-striped table-condensed">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Description</th>
                        <th>Match</th>
                        <th>TBA Key</th>
                        <th>Blue 1</th>
                        <th>Blue 2</th>
                        <th>Blue 3</th>
                        <th>Red 1</th>
                        <th>Red 2</th>
                        <th>Red 3</th>
                      </tr>
                    </thead>
                    <tbody>
                      {matches.map((match, index) => (
                        <tr key={index}>
                          <td>{match.timeString}</td>
                          <td>{match.description}</td>
                          <td>{match.rawMatchNumber}</td>
                          <td>{match.tbaMatchKey}</td>
                          <td>
                            {cleanTeamNum(
                              match.alliances.blue.teams[0].replace("frc", "")
                            )}
                          </td>
                          <td>
                            {cleanTeamNum(
                              match.alliances.blue.teams[1].replace("frc", "")
                            )}
                          </td>
                          <td>
                            {cleanTeamNum(
                              match.alliances.blue.teams[2].replace("frc", "")
                            )}
                          </td>
                          <td>
                            {cleanTeamNum(
                              match.alliances.red.teams[0].replace("frc", "")
                            )}
                          </td>
                          <td>
                            {cleanTeamNum(
                              match.alliances.red.teams[1].replace("frc", "")
                            )}
                          </td>
                          <td>
                            {cleanTeamNum(
                              match.alliances.red.teams[2].replace("frc", "")
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <button
                  className="btn btn-primary btn-lg"
                  onClick={handleSubmit}
                  disabled={uploading}
                >
                  {uploading ? "Uploading..." : "Upload Matches to TBA"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventScheduleTab;
