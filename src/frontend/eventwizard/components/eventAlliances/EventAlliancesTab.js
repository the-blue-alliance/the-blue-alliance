import React, { useState } from "react";
import PropTypes from "prop-types";

const NUM_ALLIANCES = 8;

function EventAlliancesTab({ selectedEvent, makeTrustedRequest }) {
  const [allianceSize, setAllianceSize] = useState(3);
  const [alliances, setAlliances] = useState(
    Array.from({ length: NUM_ALLIANCES }, () => ({
      captain: "",
      pick1: "",
      pick2: "",
      pick3: "",
    }))
  );
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");

  const handleAllianceSizeChange = (event) => {
    const newSize = parseInt(event.target.value);
    setAllianceSize(newSize);

    // Clear pick3 when changing to size 3
    if (newSize === 3) {
      setAlliances(
        alliances.map((alliance) => ({
          ...alliance,
          pick3: "",
        }))
      );
    }
  };

  const handleAllianceChange = (index, field, value) => {
    const newAlliances = [...alliances];
    newAlliances[index] = {
      ...newAlliances[index],
      [field]: value,
    };
    setAlliances(newAlliances);
  };

  const handleSubmit = () => {
    if (!selectedEvent) {
      setStatusMessage("Please select an event first");
      return;
    }

    setUploading(true);
    setStatusMessage("Uploading alliances...");

    // Build request body - array of alliances (each alliance is array of team keys)
    const requestBody = [];

    for (let i = 0; i < NUM_ALLIANCES; i++) {
      const alliance = alliances[i];
      const allianceTeams = [];

      if (!alliance.captain) {
        // Empty alliance
        requestBody.push([]);
        continue;
      }

      allianceTeams.push(`frc${alliance.captain}`);
      if (alliance.pick1) {
        allianceTeams.push(`frc${alliance.pick1}`);
      }
      if (alliance.pick2) {
        allianceTeams.push(`frc${alliance.pick2}`);
      }
      if (allianceSize >= 4 && alliance.pick3) {
        allianceTeams.push(`frc${alliance.pick3}`);
      }

      requestBody.push(allianceTeams);
    }

    makeTrustedRequest(
      `/api/trusted/v1/event/${selectedEvent}/alliance_selections/update`,
      JSON.stringify(requestBody),
      () => {
        setStatusMessage("Alliances uploaded successfully!");
        setUploading(false);
      },
      (error) => {
        setStatusMessage(`Error uploading alliances: ${error}`);
        setUploading(false);
      }
    );
  };

  return (
    <div className="tab-pane" id="alliances">
      <h3>Alliance Selection</h3>

      <div className="row">
        <div className="col-sm-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h4 className="panel-title">Alliance Selection Configuration</h4>
            </div>
            <div className="panel-body">
              <p>
                Input team numbers for event Alliance Selections. This will
                overwrite existing alliances.
              </p>

              <div className="form-group">
                <label>Number of teams per alliance</label>
                <div>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="alliance-size"
                      value="3"
                      checked={allianceSize === 3}
                      onChange={handleAllianceSizeChange}
                      disabled={uploading}
                    />
                    3
                  </label>
                  <label className="radio-inline">
                    <input
                      type="radio"
                      name="alliance-size"
                      value="4"
                      checked={allianceSize === 4}
                      onChange={handleAllianceSizeChange}
                      disabled={uploading}
                    />
                    4
                  </label>
                </div>
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

      <div className="row">
        <div className="col-sm-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h4 className="panel-title">Alliance Selection Data</h4>
            </div>
            <div className="panel-body">
              <div className="table-responsive">
                <table className="table table-striped">
                  <thead>
                    <tr>
                      <th>Alliance</th>
                      <th>Captain</th>
                      <th>Pick 1</th>
                      <th>Pick 2</th>
                      {allianceSize >= 4 && <th>Pick 3</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {alliances.map((alliance, index) => (
                      <tr key={index}>
                        <td>Alliance {index + 1}</td>
                        <td>
                          <input
                            type="text"
                            className="form-control"
                            placeholder={`Captain ${index + 1}`}
                            value={alliance.captain}
                            tabIndex={2 * (index + 1) - 1}
                            onChange={(e) =>
                              handleAllianceChange(
                                index,
                                "captain",
                                e.target.value
                              )
                            }
                            disabled={uploading}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            className="form-control"
                            placeholder={`Pick ${index + 1}-1`}
                            value={alliance.pick1}
                            tabIndex={2 * (index + 1)}
                            onChange={(e) =>
                              handleAllianceChange(
                                index,
                                "pick1",
                                e.target.value
                              )
                            }
                            disabled={uploading}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            className="form-control"
                            placeholder={`Pick ${index + 1}-2`}
                            value={alliance.pick2}
                            tabIndex={16 + (8 - index)}
                            onChange={(e) =>
                              handleAllianceChange(
                                index,
                                "pick2",
                                e.target.value
                              )
                            }
                            disabled={uploading}
                          />
                        </td>
                        {allianceSize >= 4 && (
                          <td>
                            <input
                              type="text"
                              className="form-control"
                              placeholder={`Pick ${index + 1}-3`}
                              value={alliance.pick3}
                              onChange={(e) =>
                                handleAllianceChange(
                                  index,
                                  "pick3",
                                  e.target.value
                                )
                              }
                              disabled={uploading}
                            />
                          </td>
                        )}
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
    </div>
  );
}

EventAlliancesTab.propTypes = {
  selectedEvent: PropTypes.string.isRequired,
  makeTrustedRequest: PropTypes.func.isRequired,
};

export default EventAlliancesTab;
