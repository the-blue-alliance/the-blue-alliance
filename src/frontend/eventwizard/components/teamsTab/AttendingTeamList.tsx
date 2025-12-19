import React, { useState, useEffect } from "react";
import { ApiTeam } from "../../constants/ApiTeam";
import TeamList from "./TeamList";

interface AttendingTeamListProps {
  selectedEvent: string | null;
  hasFetchedTeams: boolean;
  teams: ApiTeam[];
  fetchTeams: () => Promise<ApiTeam[]>; 
  updateTeams: (teams: ApiTeam[]) => void;
  showErrorMessage: (message: string) => void;
}

const AttendingTeamList: React.FC<AttendingTeamListProps> = ({
  selectedEvent,
  hasFetchedTeams,
  teams,
  fetchTeams,
  updateTeams,
  showErrorMessage,
}) => {
  const [buttonClass, setButtonClass] = useState("btn-info");

  useEffect(() => {
    if (!hasFetchedTeams) {
      setButtonClass("btn-info");
    }
  }, [hasFetchedTeams]);

  const handleUpdateAttendingTeams = async (): Promise<void> => {
    if (!selectedEvent) {
      // No valid event
      showErrorMessage(
        "Please select an event before fetching teams"
      );
      return;
    }

    try {
      setButtonClass("btn-warning");
      const data: ApiTeam[] = await fetchTeams();
      const sortedData = data.sort((a, b) => a.team_number - b.team_number);
      updateTeams(sortedData);
      setButtonClass("btn-success");
    } catch (error) {
      showErrorMessage(`${error}`);
      setButtonClass("btn-danger");
    }
  };

  let renderedTeams: React.ReactNode;
  if (hasFetchedTeams && teams.length === 0) {
    renderedTeams = <p>No teams found</p>;
  } else {
    renderedTeams = <TeamList teams={teams} />;
  }

  return (
    <div>
      <h4>Currently Attending Teams</h4>
      <button
        className={`btn ${buttonClass}`}
        onClick={handleUpdateAttendingTeams}
        disabled={!selectedEvent}
      >
        Fetch Teams
      </button>
      {renderedTeams}
    </div>
  );
};

export default AttendingTeamList;
