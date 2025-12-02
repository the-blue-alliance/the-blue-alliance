import React, { useState } from "react";
import PropTypes from "prop-types";
import { parseFmsAlliancesFile } from "../../utils/fmsAlliancesParser";

function FmsAlliancesTab({ selectedEvent, makeTrustedRequest }) {
  const [file, setFile] = useState(null);
  const [alliances, setAlliances] = useState([]);
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
    setStatusMessage("Loading...");

    try {
      const result = await parseFmsAlliancesFile(selectedFile);
      setAlliances(result.alliances);
      if (result.alliances.length > 0) {
        setStatusMessage(
          `Loaded ${result.alliances.length} alliance${result.alliances.length !== 1 ? "s" : ""}`
        );
      } else {
        setStatusMessage("No alliances found in the file.");
      }
    } catch (error) {
      setStatusMessage(`Error parsing file: ${error.message}`);
      setAlliances([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => {
    if (alliances.length === 0) {
      setStatusMessage("No alliances to submit");
      return;
    }

    setUploading(true);
    setStatusMessage("Uploading alliances...");

    makeTrustedRequest(
      `/api/trusted/v1/event/${selectedEvent}/alliance_selections/update`,
      JSON.stringify(alliances),
      () => {
        setUploading(false);
        setStatusMessage(
          `Successfully uploaded ${alliances.length} alliance${alliances.length !== 1 ? "s" : ""}!`
        );
      },
      (error) => {
        setUploading(false);
        setStatusMessage(`Error uploading alliances: ${error}`);
      }
    );
  };

  return (
    <div className="tab-pane" id="fms-alliances">
      <h3>FMS Alliances Import</h3>

      <div className="row">
        <div className="col-sm-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h4 className="panel-title">Upload FMS Alliance Report</h4>
            </div>
            <div className="panel-body">
              <p>
                Upload the FMS Rankings Report (Playoffs) Excel file containing
                alliance selections. The parser will automatically extract team
                numbers from the Teams column.
              </p>

              <div className="form-group">
                <label htmlFor="fms_alliances_file">
                  FMS Rankings Report (Playoffs) Excel File
                </label>
                <input
                  type="file"
                  id="fms_alliances_file"
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
                      : statusMessage.includes("Successfully")
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

      {alliances.length > 0 && (
        <div className="row">
          <div className="col-sm-12">
            <div className="panel panel-default">
              <div className="panel-heading">
                <h4 className="panel-title">Alliance Preview</h4>
              </div>
              <div className="panel-body">
                <div className="table-responsive">
                  <table className="table table-striped table-condensed">
                    <thead>
                      <tr>
                        <th>Alliance</th>
                        <th>Captain</th>
                        <th>Pick 1</th>
                        <th>Pick 2</th>
                        <th>Pick 3</th>
                      </tr>
                    </thead>
                    <tbody>
                      {alliances.map((alliance, index) => (
                        <tr key={index}>
                          <td>{index + 1}</td>
                          <td>
                            {alliance.length > 0
                              ? alliance[0].replace("frc", "")
                              : "-"}
                          </td>
                          <td>
                            {alliance.length > 1
                              ? alliance[1].replace("frc", "")
                              : "-"}
                          </td>
                          <td>
                            {alliance.length > 2
                              ? alliance[2].replace("frc", "")
                              : "-"}
                          </td>
                          <td>
                            {alliance.length > 3
                              ? alliance[3].replace("frc", "")
                              : "-"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <button
                  className="btn btn-primary btn-lg"
                  onClick={handleSubmit}
                  disabled={uploading || !selectedEvent}
                >
                  {uploading ? "Uploading..." : "Upload Alliances to TBA"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

FmsAlliancesTab.propTypes = {
  selectedEvent: PropTypes.string.isRequired,
  makeTrustedRequest: PropTypes.func.isRequired,
};

export default FmsAlliancesTab;
