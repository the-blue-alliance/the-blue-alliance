import React, { Component } from "react";
import { ApiTeam } from "../../constants/ApiTeam";
import ensureRequestSuccess from "../../net/EnsureRequestSuccess";
import TeamList from "./TeamList";

interface AttendingTeamListProps {
  selectedEvent: string | null;
  hasFetchedTeams: boolean;
  teams: ApiTeam[];
  updateTeams: (teams: ApiTeam[]) => void;
  showErrorMessage: (message: string) => void;
}

interface AttendingTeamListState {
  buttonClass: string;
}

class AttendingTeamList extends Component<
  AttendingTeamListProps,
  AttendingTeamListState
> {
  constructor(props: AttendingTeamListProps) {
    super(props);
    this.state = {
      buttonClass: "btn-info",
    };

    this.updateAttendingTeams = this.updateAttendingTeams.bind(this);
  }

  UNSAFE_componentWillReceiveProps(nextProps: AttendingTeamListProps): void {
    if (!nextProps.hasFetchedTeams) {
      this.setState({ buttonClass: "btn-info" });
    }
  }

  updateAttendingTeams(): void {
    if (!this.props.selectedEvent) {
      // No valid event
      this.props.showErrorMessage(
        "Please select an event before fetching teams"
      );
      return;
    }

    this.setState({ buttonClass: "btn-warning" });
    fetch(`/api/v3/event/${this.props.selectedEvent}/teams/simple`, {
      credentials: "same-origin",
    })
      .then(ensureRequestSuccess)
      .then((response) => response.json())
      .then((data: ApiTeam[]) =>
        data.sort((a, b) => a.team_number - b.team_number)
      )
      .then((data: ApiTeam[]) => this.props.updateTeams(data))
      .then(() => this.setState({ buttonClass: "btn-success" }))
      .catch((error) => {
        this.props.showErrorMessage(`${error}`);
        this.setState({ buttonClass: "btn-danger" });
      });
  }

  render(): React.ReactNode {
    let renderedTeams: React.ReactNode;
    if (this.props.hasFetchedTeams && this.props.teams.length === 0) {
      renderedTeams = <p>No teams found</p>;
    } else {
      renderedTeams = <TeamList teams={this.props.teams} />;
    }

    return (
      <div>
        <h4>Currently Attending Teams</h4>
        <button
          className={`btn ${this.state.buttonClass}`}
          onClick={this.updateAttendingTeams}
          disabled={!this.props.selectedEvent}
        >
          Fetch Teams
        </button>
        {renderedTeams}
      </div>
    );
  }
}

export default AttendingTeamList;
