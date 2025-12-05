import React, { ChangeEvent, useState } from "react";
import { parseResultsFile, ResultsMatch } from "../../utils/resultsParser";

interface FMSMatchResultsProps {
  selectedEvent: string;
  makeTrustedRequest: (
    path: string,
    body: string,
    successCallback: (response: any) => void,
    errorCallback: (error: any) => void
  ) => void;
}

const FMSMatchResults: React.FC<FMSMatchResultsProps> = ({
  selectedEvent,
  makeTrustedRequest,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [matches, setMatches] = useState<ResultsMatch[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [hasOcto, setHasOcto] = useState<boolean>(false);
  const [isDoubleElim, setIsDoubleElim] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [showConfirmDialog, setShowConfirmDialog] = useState<boolean>(false);

  const handleFileChange = async (
    event: ChangeEvent<HTMLInputElement>
  ): Promise<void> => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) {
      return;
    }

    setFile(selectedFile);
    setLoading(true);
    setStatusMessage("Loading...");

    try {
      const parsedMatches = await parseResultsFile(
        selectedFile,
        selectedEvent,
        hasOcto,
        isDoubleElim
      );

      setMatches(parsedMatches);
      if (parsedMatches.length > 0) {
        setStatusMessage(`Loaded ${parsedMatches.length} matches`);
        setShowConfirmDialog(true);
      } else {
        setStatusMessage("No matches found in the file.");
      }
    } catch (error: any) {
      setStatusMessage(`Error parsing file: ${error.message}`);
      setMatches([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAllianceCountChange = async (
    event: ChangeEvent<HTMLInputElement>
  ): Promise<void> => {
    const newHasOcto = event.target.value === "16";
    setHasOcto(newHasOcto);

    // Re-parse file with new alliance count if file is loaded
    if (file) {
      setLoading(true);
      setStatusMessage("Re-parsing with new alliance count...");
      try {
        const parsedMatches = await parseResultsFile(
          file,
          selectedEvent,
          newHasOcto,
          isDoubleElim
        );
        setMatches(parsedMatches);
        if (parsedMatches.length > 0) {
          setStatusMessage(`Loaded ${parsedMatches.length} matches`);
          setShowConfirmDialog(true);
        } else {
          setStatusMessage("No matches found in the file.");
        }
      } catch (error: any) {
        setStatusMessage(`Error parsing file: ${error.message}`);
        setMatches([]);
      } finally {
        setLoading(false);
      }
    }
  };

  const handlePlayoffFormatChange = async (
    newIsDoubleElim: boolean
  ): Promise<void> => {
    setIsDoubleElim(newIsDoubleElim);

    // Re-parse file with new playoff format if file is loaded
    if (file) {
      setLoading(true);
      setStatusMessage("Re-parsing with new playoff format...");
      try {
        const parsedMatches = await parseResultsFile(
          file,
          selectedEvent,
          hasOcto,
          newIsDoubleElim
        );
        setMatches(parsedMatches);
        if (parsedMatches.length > 0) {
          setStatusMessage(`Loaded ${parsedMatches.length} matches`);
          setShowConfirmDialog(true);
        } else {
          setStatusMessage("No matches found in the file.");
        }
      } catch (error: any) {
        setStatusMessage(`Error parsing file: ${error.message}`);
        setMatches([]);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleConfirm = (): void => {
    if (matches.length === 0) {
      setStatusMessage("No matches to submit");
      return;
    }

    setUploading(true);
    setShowConfirmDialog(false);

    // Strip out display-only fields before sending to API
    const apiMatches = matches.map((match) => ({
      comp_level: match.comp_level,
      set_number: match.set_number,
      match_number: match.match_number,
      alliances: match.alliances,
      time_string: match.time_string,
    }));

    makeTrustedRequest(
      `/api/trusted/v1/event/${selectedEvent}/matches/update`,
      JSON.stringify(apiMatches),
      () => {
        setUploading(false);
        setStatusMessage(`Successfully uploaded ${matches.length} matches!`);
        setMatches([]);
        setFile(null);
      },
      (error) => {
        setUploading(false);
        setStatusMessage(`Error uploading matches: ${error}`);
      }
    );
  };

  const handleCancel = (): void => {
    setShowConfirmDialog(false);
    setStatusMessage("Upload cancelled");
  };

  return (
    <div>
      <h4>FMS Match Results Import</h4>
      <p>
        Upload a FMS Match Results report. Note that this will overwrite data
        that currently exists for these matches.
      </p>

      <div className="row">
        <div className="col-sm-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h4 className="panel-title">Upload FMS Match Results Report</h4>
            </div>
            <div className="panel-body">
              <div className="form-group">
                <label htmlFor="results_file">FMS Results Excel File</label>
                <input
                  type="file"
                  id="results_file"
                  className="form-control"
                  accept=".xls,.xlsx"
                  onChange={handleFileChange}
                  disabled={!selectedEvent || loading || uploading}
                />
              </div>

              <div className="form-group">
                <label>Playoff Format</label>
                <div>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="playoff-format-results"
                      value="standard"
                      checked={!isDoubleElim}
                      onChange={() => handlePlayoffFormatChange(false)}
                      disabled={loading || uploading}
                    />
                    Standard Bracket
                  </label>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="playoff-format-results"
                      value="doubleelim"
                      checked={isDoubleElim}
                      onChange={() => handlePlayoffFormatChange(true)}
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
                      name="alliance-count-results"
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
                      name="alliance-count-results"
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

      {showConfirmDialog && matches.length > 0 && (
        <div className="row">
          <div className="col-sm-12">
            <div className="panel panel-warning">
              <div className="panel-heading">
                <h4 className="panel-title">Confirm Match Results Upload</h4>
              </div>
              <div className="panel-body">
                <p>
                  <strong>Review the parsed data below.</strong> This will
                  update {matches.length} match
                  {matches.length !== 1 ? "es" : ""} on TBA.
                </p>

                <div className="table-responsive">
                  <table className="table table-striped table-condensed">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Match</th>
                        <th>TBA Key</th>
                        <th>Red 1</th>
                        <th>Red 2</th>
                        <th>Red 3</th>
                        <th>Blue 1</th>
                        <th>Blue 2</th>
                        <th>Blue 3</th>
                        <th>Red Score</th>
                        <th>Blue Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {matches.map((match, index) => (
                        <tr key={index}>
                          <td>{match.timeString}</td>
                          <td>{match.description}</td>
                          <td>{match.tbaMatchKey}</td>
                          <td>{match.rawRedTeams[0]}</td>
                          <td>{match.rawRedTeams[1]}</td>
                          <td>{match.rawRedTeams[2]}</td>
                          <td>{match.rawBlueTeams[0]}</td>
                          <td>{match.rawBlueTeams[1]}</td>
                          <td>{match.rawBlueTeams[2]}</td>
                          <td>{match.alliances.red.score}</td>
                          <td>{match.alliances.blue.score}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="btn-group">
                  <button
                    className="btn btn-success btn-lg"
                    onClick={handleConfirm}
                    disabled={uploading}
                  >
                    {uploading ? "Uploading..." : "Confirm and Upload to TBA"}
                  </button>
                  <button
                    className="btn btn-default btn-lg"
                    onClick={handleCancel}
                    disabled={uploading}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FMSMatchResults;
