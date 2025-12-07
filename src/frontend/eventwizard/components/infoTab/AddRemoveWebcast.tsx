import React, { ChangeEvent, useState } from "react";
import WebcastList from "./WebcastList";
import { ApiEvent } from "../../constants/ApiEvent";

interface AddRemoveWebcastProps {
  eventInfo: ApiEvent | null;
  addWebcast: (url: string, date: string) => void;
  removeWebcast: (index: number) => void;
}

const AddRemoveWebcast: React.FC<AddRemoveWebcastProps> = ({
  eventInfo,
  addWebcast,
  removeWebcast,
}) => {
  const [newWebcastUrl, setNewWebcastUrl] = useState("");
  const [newWebcastDate, setNewWebcastDate] = useState("");

  const handleNewWebcastUrlChange = (event: ChangeEvent<HTMLInputElement>): void => {
    setNewWebcastUrl(event.target.value);
  };

  const handleNewWebcastDateChange = (event: ChangeEvent<HTMLInputElement>): void => {
    setNewWebcastDate(event.target.value);
  };

  const handleAddWebcastClick = (): void => {
    addWebcast(newWebcastUrl, newWebcastDate);
    setNewWebcastUrl("");
    setNewWebcastDate("");
  };

  let webcastList: React.ReactNode = null;
  if (eventInfo && eventInfo.webcasts && eventInfo.webcasts.length > 0) {
    webcastList = (
      <WebcastList
        webcasts={eventInfo.webcasts}
        removeWebcast={removeWebcast}
      />
    );
  } else {
    webcastList = <p>No webcasts found</p>;
  }

  return (
    <div className="form-group row">
      <label htmlFor="webcast_list" className="col-sm-2 control-label">
        Webcasts
      </label>
      <div className="col-sm-10" id="webcast_list">
        {webcastList}

        <div style={{ display: "flex", gap: "0.5em" }}>
          <input
            type="text"
            className="form-control"
            id="webcast_url"
            placeholder="https://youtu.be/abc123"
            disabled={eventInfo === null}
            onChange={handleNewWebcastUrlChange}
            value={newWebcastUrl}
          />
          <input
            type="text"
            className="form-control"
            id="webcast_date"
            placeholder="2025-03-02 (optional)"
            disabled={eventInfo === null}
            onChange={handleNewWebcastDateChange}
            value={newWebcastDate}
          />
          <button
            className="btn btn-info"
            onClick={handleAddWebcastClick}
            disabled={eventInfo === null}
          >
            Add Webcast
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddRemoveWebcast;
