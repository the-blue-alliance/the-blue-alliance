import React, { ChangeEvent, useState, useEffect } from "react";
import PlayoffTypeDropdown from "./PlayoffTypeDropdown";
import SyncCodeInput from "./SyncCodeInput";
import AddRemoveWebcast from "./AddRemoveWebcast";
import AddRemoveTeamMap from "./AddRemoveTeamMap";
import { ApiEvent } from "../../constants/ApiEvent";
import ensureRequestSuccess from "../../net/EnsureRequestSuccess";

interface EventInfoTabProps {
  selectedEvent: string | null;
  makeTrustedRequest: (
    path: string,
    body: string
  ) => Promise<Response>;
  makeApiV3Request: <T = unknown>(
    path: string
  ) => Promise<T>;
}

interface PlayoffType {
  label: string;
  value: number;
}

const EventInfoTab: React.FC<EventInfoTabProps> = ({
  selectedEvent,
  makeTrustedRequest,
  makeApiV3Request,
}) => {
  const [eventInfo, setEventInfo] = useState<ApiEvent | null>(null);
  const [status, setStatus] = useState("");
  const [buttonClass, setButtonClass] = useState("btn-primary");

  useEffect(() => {
    if (selectedEvent === null) {
      setEventInfo(null);
      setButtonClass("btn-primary");
    } else {
      loadEventInfo(selectedEvent);
      setButtonClass("btn-primary");
    }
  }, [selectedEvent]);

  const loadEventInfo = async (newEventKey: string): Promise<void> => {
    setStatus("Loading event info...");

    try {
      const data1 = await makeApiV3Request<ApiEvent>(`/api/v3/event/${newEventKey}`);

      // Merge in remap_teams
      const response2 = await fetch(`/_/remap_teams/${newEventKey}`);
      await ensureRequestSuccess(response2);
      const data2: Record<string, string> = await response2.json();

      const data = Object.assign({}, data1);
      data.remap_teams = data2;

      setEventInfo(data);
      setStatus("");
    } catch (error) {
      setStatus("");
    }
  };

  const handleFirstCodeChange = (event: ChangeEvent<HTMLInputElement>): void => {
    if (eventInfo !== null) {
      const newInfo = { ...eventInfo };
      newInfo.first_event_code = event.target.value;
      setEventInfo(newInfo);
    }
  };

  const handleSetPlayoffType = (newType: PlayoffType | null): void => {
    if (eventInfo !== null && newType !== null) {
      const newInfo = { ...eventInfo };
      newInfo.playoff_type = newType.value;
      newInfo.playoff_type_string = newType.label;
      setEventInfo(newInfo);
    }
  };

  const handleAddWebcast = (webcastUrl: string, webcastDate: string): void => {
    if (eventInfo !== null) {
      const newInfo = { ...eventInfo };
      if (!newInfo.webcasts) {
        newInfo.webcasts = [];
      }
      newInfo.webcasts.push({
        type: "",
        channel: "",
        url: webcastUrl,
        date: webcastDate ? webcastDate : undefined,
      });
      setEventInfo(newInfo);
    }
  };

  const handleRemoveWebcast = (indexToRemove: number): void => {
    if (eventInfo !== null && eventInfo.webcasts) {
      const newInfo = { ...eventInfo };
      newInfo.webcasts.splice(indexToRemove, 1);
      setEventInfo(newInfo);
    }
  };

  const handleAddTeamMap = (fromTeamKey: string, toTeamKey: string): void => {
    if (eventInfo !== null) {
      const newInfo = { ...eventInfo };
      if (!newInfo.remap_teams) {
        newInfo.remap_teams = {};
      }
      newInfo.remap_teams[fromTeamKey] = toTeamKey;
      setEventInfo(newInfo);
    }
  };

  const handleRemoveTeamMap = (keyToRemove: string): void => {
    if (eventInfo !== null && eventInfo.remap_teams) {
      const newInfo = { ...eventInfo };
      delete newInfo.remap_teams[keyToRemove];
      setEventInfo(newInfo);
    }
  };

  const handleUpdateEventInfo = async (): Promise<void> => {
    setButtonClass("btn-warning");
    try {
      await makeTrustedRequest(
        `/api/trusted/v1/event/${selectedEvent}/info/update`,
        JSON.stringify(eventInfo)
      );
      setButtonClass("btn-success");
    } catch (error) {
      alert(`Error: ${error}`);
    }
  };

  return (
    <div className="tab-pane active col-xs-12" id="info">
      <h3>Event Info</h3>
      {status && <p>{status}</p>}
      <div className="row" style={{ marginInline: "0" }}>
        <PlayoffTypeDropdown
          eventInfo={eventInfo}
          setType={handleSetPlayoffType}
        />

        <SyncCodeInput
          eventInfo={eventInfo}
          setSyncCode={handleFirstCodeChange}
        />

        <AddRemoveWebcast
          eventInfo={eventInfo}
          addWebcast={handleAddWebcast}
          removeWebcast={handleRemoveWebcast}
        />

        <AddRemoveTeamMap
          eventInfo={eventInfo}
          addTeamMap={handleAddTeamMap}
          removeTeamMap={handleRemoveTeamMap}
        />

        <button
          className={`btn ${buttonClass}`}
          onClick={handleUpdateEventInfo}
          disabled={eventInfo === null}
        >
          Publish Changes
        </button>
      </div>
    </div>
  );
};

export default EventInfoTab;
