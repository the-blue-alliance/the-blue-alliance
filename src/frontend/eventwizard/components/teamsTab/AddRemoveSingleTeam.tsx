import React, { useState, useEffect } from "react";
import AsyncSelect from "react-select/async";
import { ApiTeam } from "../../constants/ApiTeam";

interface TeamOption {
  value: string;
  label: string;
}

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
  const [teamOptions, setTeamOptions] = useState<TeamOption[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<TeamOption | null>(null);
  const [selectedTeamKey, setSelectedTeamKey] = useState("");
  const [addButtonClass, setAddButtonClass] = useState("btn-primary");
  const [removeButtonClass, setRemoveButtonClass] = useState("btn-primary");

  useEffect(() => {
    // Load team typeahead data
    const loadTeamsData = async () => {
      const resp = await fetch("/_/typeahead/teams-all");
      const json: string[] = await resp.json();
      const options = json.map((team) => {
        const teamNumber = team.split("|")[0].trim();
        return {
          value: `frc${teamNumber}`,
          label: team,
        };
      });
      setTeamOptions(options);
    };
    loadTeamsData();
  }, []);

  useEffect(() => {
    if (!hasFetchedTeams) {
      setAddButtonClass("btn-primary");
      setRemoveButtonClass("btn-primary");
    }
  }, [hasFetchedTeams]);

  const loadTeams = async (search: string): Promise<TeamOption[]> => {
    return teamOptions.filter((team) =>
      team.label.toLowerCase().includes(search.toLowerCase())
    );
  };

  const handleTeamSelectionChanged = (newTeam: TeamOption | null): void => {
    setSelectedTeam(newTeam);
    if (newTeam) {
      setSelectedTeamKey(newTeam.value);
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
        setSelectedTeam(null);
        setSelectedTeamKey("");
        hasFetchedTeams = false;
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
        setSelectedTeam(null);
        setSelectedTeamKey("");
        hasFetchedTeams = false;
        if (clearTeams) {
          clearTeams();
        }
      },
      (error: string) => showErrorMessage(`${error}`)
    );
  };

  const isTeamAttending = (selectedTeam !== null && currentTeams.some(team => team.key === selectedTeam.value));

  return (
    <div>
      <h4>Add/Remove Single Team</h4>
      {selectedEvent && !hasFetchedTeams && (
        <p>
          <em>Note:</em> Please fetch the current team list before adding or
          removing a team
        </p>
      )}
      <AsyncSelect<TeamOption>
        name="selectTeam"
        placeholder="Enter team name or number..."
        noOptionsMessage={() => "Start typing..."}
        value={selectedTeam}
        loadOptions={loadTeams}
        defaultOptions={teamOptions}
        onChange={handleTeamSelectionChanged}
        isDisabled={!selectedEvent || !hasFetchedTeams}
      />
      <button
        className={`btn ${addButtonClass}`}
        onClick={handleAddSingleTeam}
        disabled={
          !selectedEvent ||
          !hasFetchedTeams ||
          !selectedTeamKey || 
          isTeamAttending
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
          !selectedTeamKey ||
          !isTeamAttending
        }
      >
        Remove Team
      </button>
    </div>
  );
};

export default AddRemoveSingleTeam;
