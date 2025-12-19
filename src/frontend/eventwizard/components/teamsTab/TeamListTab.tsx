import React, { useState, useEffect } from "react";
import Button from "react-bootstrap/Button";
import Modal from "react-bootstrap/Modal";
import { ApiTeam } from "../../constants/ApiTeam";

import AddRemoveSingleTeam from "./AddRemoveSingleTeam";
import AddMultipleTeams from "./AddMultipleTeams";
import AddTeamsFMSReport from "./AddTeamsFMSReport";
import AttendingTeamList from "./AttendingTeamList";

interface TeamListTabProps {
  selectedEvent: string | null;
  makeTrustedRequest: (
    path: string,
    body: string | FormData
  ) => Promise<Response>;
  makeApiV3Request: (
    path: string,
  ) => Promise<Response>;
}

const TeamListTab: React.FC<TeamListTabProps> = ({
  selectedEvent,
  makeApiV3Request,
  makeTrustedRequest,
}) => {
  const [teams, setTeams] = useState<ApiTeam[]>([]);
  const [hasFetchedTeams, setHasFetchedTeams] = useState(false);
  const [showErrorDialog, setShowErrorDialog] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (selectedEvent !== null) {
      handleClearTeams();
    }
  }, [selectedEvent]);

  const handleUpdateTeamList = async (
    teamKeys: string[],
    onSuccess: () => void,
    onError: (error: string) => void
  ): Promise<void> => {
    if (!selectedEvent) return;
    try {
      await makeTrustedRequest(
        `/api/trusted/v1/event/${selectedEvent}/team_list/update`,
        JSON.stringify(teamKeys)
      );
      onSuccess();
    } catch (error) {
      onError(String(error));
    }
  };

  const handleShowError = (message: string): void => {
    setShowErrorDialog(true);
    setErrorMessage(message);
  };

  const handleClearError = (): void => {
    setShowErrorDialog(false);
    setErrorMessage("");
  };

  const handleUpdateTeams = (newTeams: ApiTeam[]): void => {
    setTeams(newTeams);
    setHasFetchedTeams(true);
  };

  const handleFetchTeams = async (): Promise<ApiTeam[]> => {
    if (!selectedEvent) {
      return [];
    }
    const response = await makeApiV3Request(
      `/api/v3/event/${selectedEvent}/teams/simple`
    );
    if (!response.ok) {
      setErrorMessage(`Error fetching teams: ${response.statusText}`);
      setShowErrorDialog(true);
      return [];
    }
    const data: ApiTeam[] = await response.json();
    return data;
  }

  const handleClearTeams = (): void => {
    setTeams([]);
    setHasFetchedTeams(false);
  };

  return (
    <div className="tab-pane" id="teams">
      <Modal
        show={showErrorDialog}
        onHide={handleClearError}
        backdrop={false}
        animation={false}
        centered={true}
      >
        <Modal.Header>
          <Modal.Title>Error!</Modal.Title>
        </Modal.Header>
        <Modal.Body>{errorMessage}</Modal.Body>
        <Modal.Footer>
          <Button variant="primary" onClick={handleClearError}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      <h3>Team List</h3>
      <div className="row">
        <div className="col-sm-6">
          <AddTeamsFMSReport
            selectedEvent={selectedEvent}
            updateTeamList={handleUpdateTeamList}
            showErrorMessage={handleShowError}
            clearTeams={handleClearTeams}
            makeTrustedRequest={makeTrustedRequest}
          />
          <hr />

          <AddRemoveSingleTeam
            selectedEvent={selectedEvent}
            updateTeamList={handleUpdateTeamList}
            showErrorMessage={handleShowError}
            hasFetchedTeams={hasFetchedTeams}
            currentTeams={teams}
            clearTeams={handleClearTeams}
          />
          <hr />

          <AddMultipleTeams
            selectedEvent={selectedEvent}
            updateTeamList={handleUpdateTeamList}
            showErrorMessage={handleShowError}
            clearTeams={handleClearTeams}
          />
        </div>
        <div className="col-sm-6">
          <AttendingTeamList
            selectedEvent={selectedEvent}
            hasFetchedTeams={hasFetchedTeams}
            teams={teams}
            fetchTeams={handleFetchTeams}
            updateTeams={handleUpdateTeams}
            showErrorMessage={handleShowError}
          />
        </div>
      </div>
    </div>
  );
};

export default TeamListTab;
