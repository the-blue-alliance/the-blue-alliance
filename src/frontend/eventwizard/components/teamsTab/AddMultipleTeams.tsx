import React, { ChangeEvent, useState } from "react";

interface AddMultipleTeamsProps {
  selectedEvent: string | null;
  clearTeams?: () => void;
  updateTeamList: (
    teams: string[],
    successCallback: () => void,
    errorCallback: (error: string) => void
  ) => void;
  showErrorMessage: (message: string) => void;
}

const AddMultipleTeams: React.FC<AddMultipleTeamsProps> = ({
  selectedEvent,
  clearTeams,
  updateTeamList,
  showErrorMessage,
}) => {
  const [inputTeams, setInputTeams] = useState("");
  const [buttonClass, setButtonClass] = useState("btn-primary");

  const handleInputChange = (event: ChangeEvent<HTMLTextAreaElement>): void => {
    setInputTeams(event.target.value);
  };

  const handleAddTeams = (): void => {
    if (!selectedEvent) {
      // No valid event
      showErrorMessage("Please select an event before adding teams");
      return;
    }

    const teams: string[] = [];
    const teamInput = inputTeams.split("\n");
    for (let i = 0; inputTeams && i < teamInput.length; i++) {
      const teamNum = parseInt(teamInput[i], 10);
      if (!teamNum || isNaN(teamNum) || teamNum <= 0 || teamNum > 9999) {
        showErrorMessage(`Invalid team ${teamInput[i]}`);
        return;
      }
      teams.push(`frc${teamNum}`);
    }

    setButtonClass("btn-warning");
    updateTeamList(
      teams,
      () => {
        setButtonClass("btn-success");
        if (clearTeams) {
          clearTeams();
        }
      },
      (error: string) => showErrorMessage(`${error}`)
    );
  };

  return (
    <div>
      <h4>Add Multiple Teams</h4>
      <p>
        Enter a list of team numbers, one per line. This will{" "}
        <em>overwrite</em> all existing teams for this event.
      </p>
      <textarea
        className="form-control"
        value={inputTeams}
        onChange={handleInputChange}
      />
      <button
        className={`btn ${buttonClass}`}
        onClick={handleAddTeams}
        disabled={!selectedEvent}
      >
        Overwrite Teams
      </button>
    </div>
  );
};

export default AddMultipleTeams;
