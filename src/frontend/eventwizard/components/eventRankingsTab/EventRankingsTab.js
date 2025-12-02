import React, { useState } from "react";
import PropTypes from "prop-types";
import { parseRankingsFile } from "../../utils/rankingsParser";

function EventRankingsTab({ selectedEvent, makeTrustedRequest }) {
  const [file, setFile] = useState(null);
  const [rankings, setRankings] = useState([]);
  const [breakdowns, setBreakdowns] = useState([]);
  const [headers, setHeaders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  const handleFileChange = async (event) => {
    const selectedFile = event.target.files[0];
    if (!selectedFile) {
      return;
    }

    setFile(selectedFile);
    setLoading(true);
    setStatusMessage("Loading rankings...");

    try {
      const result = await parseRankingsFile(selectedFile);
      setRankings(result.rankings);
      setBreakdowns(result.breakdowns);
      setHeaders(result.headers);
      setStatusMessage(
        `Loaded rankings for ${result.rankings.length} teams with ${result.breakdowns.length} breakdown columns`
      );
    } catch (error) {
      setStatusMessage(`Error parsing file: ${error.message}`);
      setRankings([]);
      setBreakdowns([]);
      setHeaders([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => {
    if (!selectedEvent) {
      alert("Please select an event first");
      return;
    }

    if (rankings.length === 0) {
      alert("No rankings to upload");
      return;
    }

    setUploading(true);
    setStatusMessage("Uploading rankings...");

    const requestBody = {
      breakdowns: breakdowns,
      rankings: rankings,
    };

    makeTrustedRequest(
      `/api/trusted/v1/event/${selectedEvent}/rankings/update`,
      JSON.stringify(requestBody),
      () => {
        setStatusMessage("Rankings uploaded successfully!");
        setUploading(false);
      },
      (error) => {
        setStatusMessage(`Error uploading rankings: ${error}`);
        setUploading(false);
      }
    );
  };

  return (
    <div className="tab-pane" id="rankings">
      <h3>FMS Rankings Import</h3>

      <div className="row">
        <div className="col-sm-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h4 className="panel-title">Upload FMS Rankings Report</h4>
            </div>
            <div className="panel-body">
              <p>
                Upload event rankings from FMS report. This will overwrite
                current rankings for that event.
              </p>

              <div className="form-group">
                <label htmlFor="rankings_file">FMS Rankings Excel File</label>
                <input
                  type="file"
                  id="rankings_file"
                  className="form-control"
                  accept=".xls,.xlsx"
                  onChange={handleFileChange}
                  disabled={!selectedEvent || loading || uploading}
                />
              </div>

              {statusMessage && (
                <div
                  className={`alert ${
                    statusMessage.includes("Error")
                      ? "alert-danger"
                      : statusMessage.includes("successfully")
                        ? "alert-success"
                        : "alert-info"
                  }`}
                >
                  {statusMessage}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {rankings.length > 0 && (
        <div className="row">
          <div className="col-sm-12">
            <div className="panel panel-default">
              <div className="panel-heading">
                <h4 className="panel-title">Rankings Preview</h4>
              </div>
              <div className="panel-body">
                <div className="table-responsive">
                  <table className="table table-striped table-condensed">
                    <thead>
                      <tr>
                        {headers.map((header) => (
                          <th key={header}>{header}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rankings.map((ranking, index) => (
                        <tr key={index}>
                          {headers.map((header) => {
                            // Map internal field names back to original headers
                            let value = "";
                            const headerLower = header.toLowerCase();

                            if (headerLower.includes("rank")) {
                              value = ranking.rank;
                            } else if (headerLower.includes("team")) {
                              value = ranking.team_key.replace("frc", "");
                            } else if (
                              headerLower.includes("w-l-t") ||
                              headerLower.includes("wlt")
                            ) {
                              value = `${ranking.wins}-${ranking.losses}-${ranking.ties}`;
                            } else if (headerLower.includes("dq")) {
                              value = ranking.dqs;
                            } else if (headerLower.includes("played")) {
                              value = ranking.played;
                            } else {
                              // Breakdown column
                              value = ranking[header] ?? "";
                            }

                            return <td key={header}>{value}</td>;
                          })}
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
                  {uploading ? "Uploading..." : "Upload Rankings to TBA"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

EventRankingsTab.propTypes = {
  selectedEvent: PropTypes.string.isRequired,
  makeTrustedRequest: PropTypes.func.isRequired,
};

export default EventRankingsTab;
