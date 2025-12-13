import React, { useState, useEffect, useRef } from "react";
import { Typeahead } from "react-bootstrap-typeahead";
import { ApiTeam } from "../../constants/ApiTeam";

interface AddRemoveSingleTeamProps {
  selectedEvent: string | null;
  updateTeamList: (
    teamKeys: string[],
    onSuccess: () => void,
    onError: (error: string) => void
  ) => void;
  hasFetchedTeams: boolean;
  currentTeams: ApiTeam[];
  clearTeams?: () => void;
  showErrorMessage: (message: string) => void;
}

const AddRemoveSingleTeam: React.FC<AddRemoveSingleTeamProps> = ({
  selectedEvent,
  updateTeamList,
  hasFetchedTeams,
  currentTeams,
  clearTeams,
  showErrorMessage,
}) => {
  const [teamTypeaheadOptions, setTeamTypeaheadOptions] = useState<string[]>([]);
  const [selectedTeamKey, setSelectedTeamKey] = useState("");
  const [addButtonClass, setAddButtonClass] = useState("btn-primary");
  const [removeButtonClass, setRemoveButtonClass] = useState("btn-primary");
  const teamTypeahead = useRef<any>(null);

  useEffect(() => {
    // Load team typeahead data
    const loadTeams = async () => {
      const resp = await fetch("/_/typeahead/teams-all");
      const json: string[] = await resp.json();
      setTeamTypeaheadOptions(json);
    };
    loadTeams();
  }, []);

  useEffect(() => {
    if (!hasFetchedTeams) {
      setAddButtonClass("btn-primary");
      setRemoveButtonClass("btn-primary");
    }
  }, [hasFetchedTeams]);

  const handleTeamSelectionChanged = (selected: any[]): void => {
    if (selected && selected.length > 0) {
      const teamValue = typeof selected[0] === 'string' ? selected[0] : String(selected[0]);
      const teamNumber = teamValue.split("|")[0].trim();
      setSelectedTeamKey(`frc${teamNumber}`);
    } else {
      setSelectedTeamKey("");
    }
  };

  const handleAddSingleTeam = (): void => {
    if (!hasFetchedTeams) {
      showErrorMessage(
        "Please fetch teams before modification to ensure up to date data"
      );
      return;
    }

    const existingTeamKeys = currentTeams.map((team) => team.key);
    const keyIndex = existingTeamKeys.indexOf(selectedTeamKey);
    if (keyIndex >= 0) {
      showErrorMessage(
        `Team ${selectedTeamKey} is already attending ${selectedEvent}. Re-fetch the team list if you know this is wrong.`
      );
      return;
    }

    existingTeamKeys.push(selectedTeamKey);
    setAddButtonClass("btn-warning");
    updateTeamList(
      existingTeamKeys,
      () => {
        setAddButtonClass("btn-success");
        teamTypeahead.current?.clear();
        if (clearTeams) {
          clearTeams();
        }
      },
      (error: string) => showErrorMessage(`${error}`)
    );
  };

  const handleRemoveSingleTeam = (): void => {
    if (!hasFetchedTeams) {
      showErrorMessage(
        "Please fetch teams before modification to ensure up to date data"
      );
      return;
    }

    const existingTeamKeys = currentTeams.map((team) => team.key);
    const keyIndex = existingTeamKeys.indexOf(selectedTeamKey);
    if (keyIndex < 0) {
      showErrorMessage(
        `Team ${selectedTeamKey} is already not attending ${selectedEvent}. Re-fetch the team list if you know this is wrong.`
      );
      return;
    }

    existingTeamKeys.splice(keyIndex, 1);
    setRemoveButtonClass("btn-warning");
    updateTeamList(
      existingTeamKeys,
      () => {
        setRemoveButtonClass("btn-success");
        teamTypeahead.current?.clear();
        if (clearTeams) {
          clearTeams();
        }
      },
      (error: string) => showErrorMessage(`${error}`)
    );
  };

  return (
    <div>
      <h4>Add/Remove Single Team</h4>
      {selectedEvent && !hasFetchedTeams && (
        <p>
          <em>Note:</em> Please fetch the current team list before adding or
          removing a team
        </p>
      )}
      <Typeahead
        ref={teamTypeahead}
        id="teamTypeahead"
        placeholder="Enter team name or number..."
        options={teamTypeaheadOptions}
        onChange={handleTeamSelectionChanged}
        disabled={!selectedEvent}
      />
      <button
        className={`btn ${addButtonClass}`}
        onClick={handleAddSingleTeam}
        disabled={
          !selectedEvent ||
          !hasFetchedTeams ||
          !selectedTeamKey
        }
      >
        Add Team
      </button>
      <button
        className={`btn ${removeButtonClass}`}
        onClick={handleRemoveSingleTeam}
        disabled={
          !selectedEvent ||
          !hasFetchedTeams ||
          !selectedTeamKey
        }
      >
        Remove Team
      </button>
    </div>
  );
};

export default AddRemoveSingleTeam;
