import React, { useState } from "react";
import PropTypes from "prop-types";
import EventManualAlliances from "./EventManualAlliances";
import FMSAllianceImport from "./FMSAllianceImport";

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

  const handleManualSubmit = () => {
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

  const handleFMSImport = (alliancesData, onSuccess, onError) => {
    makeTrustedRequest(
      `/api/trusted/v1/event/${selectedEvent}/alliance_selections/update`,
      JSON.stringify(alliancesData),
      onSuccess,
      onError
    );
  };

  return (
    <div className="tab-pane" id="alliances">
      <h3>Alliance Selection</h3>

      <div className="row">
        <div className="col-sm-12">
          <div className="panel panel-default">
            <div className="panel-heading">
              <h4 className="panel-title">FMS Alliance Import</h4>
            </div>
            <div className="panel-body">
              <FMSAllianceImport
                selectedEvent={selectedEvent}
                updateAlliances={handleFMSImport}
              />
            </div>
          </div>
        </div>
      </div>

      <EventManualAlliances
        allianceSize={allianceSize}
        alliances={alliances}
        uploading={uploading}
        selectedEvent={selectedEvent}
        onAllianceSizeChange={handleAllianceSizeChange}
        onAllianceChange={handleAllianceChange}
        onSubmit={handleManualSubmit}
        statusMessage={statusMessage}
      />
    </div>
  );
}

EventAlliancesTab.propTypes = {
  selectedEvent: PropTypes.string.isRequired,
  makeTrustedRequest: PropTypes.func.isRequired,
};

export default EventAlliancesTab;
