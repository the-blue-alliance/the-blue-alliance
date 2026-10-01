import React, { useState, useEffect } from "react";
import AsyncSelect from "react-select/async";
import { ApiTeam } from "../../constants/ApiTeam";
import { editSingleTeam } from "../../utils/singleTeamEdit";

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
  hasFetchedTeams: teamsFetched,
  currentTeams,
  clearTeams,
  showErrorMessage,
}) => {
  const [teamOptions, setTeamOptions] = useState<TeamOption[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<TeamOption | null>(null);
  const [selectedTeamKey, setSelectedTeamKey] = useState("");
  const [addButtonClass, setAddButtonClass] = useState("btn-primary");
  const [removeButtonClass, setRemoveButtonClass] = useState("btn-primary");
  // The team list is stale after an edit until the parent fetches it again.
  const [isStale, setIsStale] = useState(false);
  useEffect(() => setIsStale(false), [currentTeams]);
  const hasFetchedTeams = teamsFetched && !isStale;

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
    if (!teamsFetched) {
      setAddButtonClass("btn-primary");
      setRemoveButtonClass("btn-primary");
    }
  }, [teamsFetched]);

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

  const submitTeamList = (
    teamKeys: string[],
    setButtonClass: (buttonClass: string) => void
  ): void => {
    setButtonClass("btn-warning");
    updateTeamList(
      teamKeys,
      () => {
        setButtonClass("btn-success");
        setSelectedTeam(null);
        setSelectedTeamKey("");
        setIsStale(true);
        if (clearTeams) {
          clearTeams();
        }
      },
      (error: string) => showErrorMessage(`${error}`)
    );
  };

  const editRequest = {
    eventKey: selectedEvent,
    teamKey: selectedTeamKey,
    currentTeamKeys: currentTeams.map((team) => team.key),
    hasFetchedTeams,
  };

  const handleAddSingleTeam = (): void =>
    editSingleTeam(
      "add",
      editRequest,
      (teamKeys) => submitTeamList(teamKeys, setAddButtonClass),
      showErrorMessage
    );

  const handleRemoveSingleTeam = (): void =>
    editSingleTeam(
      "remove",
      editRequest,
      (teamKeys) => submitTeamList(teamKeys, setRemoveButtonClass),
      showErrorMessage
    );

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
