import React, { ChangeEvent, useState } from "react";
import EventManualAlliances from "./EventManualAlliances";
import FMSAllianceImport from "./FMSAllianceImport";

const NUM_ALLIANCES = 8;

interface Alliance {
  captain: string;
  pick1: string;
  pick2: string;
  pick3: string;
}

interface EventAlliancesTabProps {
  selectedEvent: string;
  makeTrustedRequest: (
    path: string,
    body: string,
    successCallback: (response: any) => void,
    errorCallback: (error: any) => void
  ) => void;
}

const EventAlliancesTab: React.FC<EventAlliancesTabProps> = ({
  selectedEvent,
  makeTrustedRequest,
}) => {
  const [allianceSize, setAllianceSize] = useState<number>(3);
  const [alliances, setAlliances] = useState<Alliance[]>(
    Array.from({ length: NUM_ALLIANCES }, () => ({
      captain: "",
      pick1: "",
      pick2: "",
      pick3: "",
    }))
  );
  const [uploading, setUploading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>("");

  const handleAllianceSizeChange = (
    event: ChangeEvent<HTMLInputElement>
  ): void => {
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

  const handleAllianceChange = (
    index: number,
    field: keyof Alliance,
    value: string
  ): void => {
    const newAlliances = [...alliances];
    newAlliances[index] = {
      ...newAlliances[index],
      [field]: value,
    };
    setAlliances(newAlliances);
  };

  const handleManualSubmit = (): void => {
    if (!selectedEvent) {
      setStatusMessage("Please select an event first");
      return;
    }

    setUploading(true);
    setStatusMessage("Uploading alliances...");

    // Build request body - array of alliances (each alliance is array of team keys)
    const requestBody: string[][] = [];

    for (let i = 0; i < NUM_ALLIANCES; i++) {
      const alliance = alliances[i];
      const allianceTeams: string[] = [];

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

  const handleFMSImport = (
    alliancesData: string[][],
    onSuccess: () => void,
    onError: (error: string) => void
  ): void => {
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
};

export default EventAlliancesTab;
