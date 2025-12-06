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

  async updateAttendingTeams(): Promise<void> {
    if (!this.props.selectedEvent) {
      // No valid event
      this.props.showErrorMessage(
        "Please select an event before fetching teams"
      );
      return;
    }

    try {
      this.setState({ buttonClass: "btn-warning" });
      const response = await fetch(`/api/v3/event/${this.props.selectedEvent}/teams/simple`, {
        credentials: "same-origin",
      });
      await ensureRequestSuccess(response);
      const data: ApiTeam[] = await response.json();
      const sortedData = data.sort((a, b) => a.team_number - b.team_number);
      this.props.updateTeams(sortedData);
      this.setState({ buttonClass: "btn-success" });
    } catch (error) {
      this.props.showErrorMessage(`${error}`);
      this.setState({ buttonClass: "btn-danger" });
    }
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
