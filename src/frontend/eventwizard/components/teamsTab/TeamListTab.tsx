import React, { Component } from "react";
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
    body: string
  ) => Promise<Response>;
}

interface TeamListTabState {
  teams: ApiTeam[];
  hasFetchedTeams: boolean;
  addMultipleButtonStatus: string;
  showErrorDialog: boolean;
  errorMessage: string;
}

class TeamListTab extends Component<TeamListTabProps, TeamListTabState> {
  constructor(props: TeamListTabProps) {
    super(props);
    this.state = {
      teams: [],
      hasFetchedTeams: false,
      addMultipleButtonStatus: "btn-primary",
      showErrorDialog: false,
      errorMessage: "",
    };
    this.showError = this.showError.bind(this);
    this.clearError = this.clearError.bind(this);
    this.updateTeams = this.updateTeams.bind(this);
    this.clearTeams = this.clearTeams.bind(this);
    this.updateTeamList = this.updateTeamList.bind(this);
  }

  UNSAFE_componentWillReceiveProps(nextProps: TeamListTabProps): void {
    if (this.props.selectedEvent !== nextProps.selectedEvent) {
      this.clearTeams();
    }
  }

  async updateTeamList(
    teamKeys: string[],
    onSuccess: () => void,
    onError: (error: string) => void
  ): Promise<void> {
    if (!this.props.selectedEvent) return;
    try {
      await this.props.makeTrustedRequest(
        `/api/trusted/v1/event/${this.props.selectedEvent}/team_list/update`,
        JSON.stringify(teamKeys)
      );
      onSuccess();
    } catch (error) {
      onError(String(error));
    }
  }

  showError(errorMessage: string): void {
    this.setState({ showErrorDialog: true, errorMessage: errorMessage });
  }

  clearError(): void {
    this.setState({ showErrorDialog: false, errorMessage: "" });
  }

  updateTeams(teams: ApiTeam[]): void {
    this.setState({ teams, hasFetchedTeams: true });
  }

  clearTeams(): void {
    this.setState({ teams: [], hasFetchedTeams: false });
  }

  render(): React.ReactNode {
    return (
      <div className="tab-pane" id="teams">
        <Modal
          show={this.state.showErrorDialog}
          onHide={this.clearError}
          backdrop={false}
          animation={false}
          centered={true}
        >
          <Modal.Header>
            <Modal.Title>Error!</Modal.Title>
          </Modal.Header>
          <Modal.Body>{this.state.errorMessage}</Modal.Body>
          <Modal.Footer>
            <Button variant="primary" onClick={this.clearError}>
              Close
            </Button>
          </Modal.Footer>
        </Modal>

        <h3>Team List</h3>
        <div className="row">
          <div className="col-sm-6">
            <AddTeamsFMSReport
              selectedEvent={this.props.selectedEvent}
              updateTeamList={this.updateTeamList}
              showErrorMessage={this.showError}
              clearTeams={this.clearTeams}
            />
            <hr />

            <AddRemoveSingleTeam
              selectedEvent={this.props.selectedEvent}
              updateTeamList={this.updateTeamList}
              showErrorMessage={this.showError}
              hasFetchedTeams={this.state.hasFetchedTeams}
              currentTeams={this.state.teams}
              clearTeams={this.clearTeams}
            />
            <hr />

            <AddMultipleTeams
              selectedEvent={this.props.selectedEvent}
              updateTeamList={this.updateTeamList}
              showErrorMessage={this.showError}
              clearTeams={this.clearTeams}
            />
          </div>
          <div className="col-sm-6">
            <AttendingTeamList
              selectedEvent={this.props.selectedEvent}
              hasFetchedTeams={this.state.hasFetchedTeams}
              teams={this.state.teams}
              updateTeams={this.updateTeams}
              showErrorMessage={this.showError}
            />
          </div>
        </div>
      </div>
    );
  }
}

export default TeamListTab;
