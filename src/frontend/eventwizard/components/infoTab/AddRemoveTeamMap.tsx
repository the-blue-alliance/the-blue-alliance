import React, { ChangeEvent, useState } from "react";
import TeamMappingsList from "./TeamMappingsList";
import { ApiEvent } from "../../constants/ApiEvent";

interface AddRemoveTeamMapProps {
  eventInfo: ApiEvent | null;
  addTeamMap: (fromTeamKey: string, toTeamKey: string) => void;
  removeTeamMap: (fromTeamKey: string) => void;
}

const AddRemoveTeamMap: React.FC<AddRemoveTeamMapProps> = ({
  eventInfo,
  addTeamMap,
  removeTeamMap,
}) => {
  const [nextFromTeam, setNextFromTeam] = useState("");
  const [nextToTeam, setNextToTeam] = useState("");
  const [fromError, setFromError] = useState(false);
  const [toError, setToError] = useState(false);

  const handleNextFromTeamChange = (event: ChangeEvent<HTMLInputElement>): void => {
    const match = event.target.value.match(/\d+/);
    setNextFromTeam(event.target.value);
    setFromError(!match || match[0] !== event.target.value);
  };

  const handleNextToTeamChange = (event: ChangeEvent<HTMLInputElement>): void => {
    const match = event.target.value.match(/\d+[b-zB-Z]?/);
    setNextToTeam(event.target.value);
    setToError(!match || match[0] !== event.target.value);
  };

  const handleAddTeamMapClick = (): void => {
    addTeamMap(
      `frc${nextFromTeam.toUpperCase()}`,
      `frc${nextToTeam.toUpperCase()}`
    );
    setNextFromTeam("");
    setNextToTeam("");
    setFromError(false);
    setToError(false);
  };

  let teamMappingsList: React.ReactNode = null;
  if (
    eventInfo &&
    eventInfo.remap_teams &&
    Object.keys(eventInfo.remap_teams).length > 0
  ) {
    teamMappingsList = (
      <TeamMappingsList
        teamMappings={eventInfo.remap_teams}
        removeTeamMap={removeTeamMap}
      />
    );
  } else {
    teamMappingsList = <p>No team mappings found</p>;
  }

  return (
    <div className="form-group row">
      <label htmlFor="team_mappings_list" className="col-sm-2 control-label">
        Team Mappings
        <br />
        <small>Note: Removing a mapping will not unmap existing data!</small>
      </label>
      <div className="col-sm-10" id="team_mappings_list">
        {teamMappingsList}

        <div
          className={
            fromError || toError
              ? "input-group has-error"
              : "input-group"
          }
        >
          <input
            className="form-control"
            type="text"
            placeholder="9254"
            disabled={eventInfo === null}
            onChange={handleNextFromTeamChange}
            value={nextFromTeam}
          />
          <span className="input-group-addon">
            <span
              className="glyphicon glyphicon-arrow-right"
              aria-hidden="true"
            />
          </span>
          <input
            className="form-control"
            type="text"
            placeholder="254B"
            disabled={eventInfo === null}
            onChange={handleNextToTeamChange}
            value={nextToTeam}
          />
          <span className="input-group-btn">
            <button
              className="btn btn-info"
              onClick={handleAddTeamMapClick}
              disabled={
                eventInfo === null ||
                fromError ||
                toError
              }
            >
              Add Mapping
            </button>
          </span>
        </div>
      </div>
    </div>
  );
};

export default AddRemoveTeamMap;
