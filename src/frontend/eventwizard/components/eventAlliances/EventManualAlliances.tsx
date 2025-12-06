import React, { ChangeEvent } from "react";

interface Alliance {
  captain: string;
  pick1: string;
  pick2: string;
  pick3: string;
}

interface EventManualAlliancesProps {
  allianceSize: number;
  alliances: Alliance[];
  uploading: boolean;
  selectedEvent: string | null;
  onAllianceSizeChange: (event: ChangeEvent<HTMLInputElement>) => void;
  onAllianceChange: (index: number, field: keyof Alliance, value: string) => void;
  onSubmit: () => void;
  statusMessage?: string;
}

const EventManualAlliances: React.FC<EventManualAlliancesProps> = ({
  allianceSize,
  alliances,
  uploading,
  selectedEvent,
  onAllianceSizeChange,
  onAllianceChange,
  onSubmit,
  statusMessage,
}) => {
  return (
    <div>
      <div className="row">
        <div className="col-sm-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h4 className="panel-title">Manual Alliance Entry</h4>
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
                      onChange={onAllianceSizeChange}
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
                      onChange={onAllianceSizeChange}
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
                              onAllianceChange(index, "captain", e.target.value)
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
                              onAllianceChange(index, "pick1", e.target.value)
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
                              onAllianceChange(index, "pick2", e.target.value)
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
                                onAllianceChange(index, "pick3", e.target.value)
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
                onClick={onSubmit}
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
};

export default EventManualAlliances;
