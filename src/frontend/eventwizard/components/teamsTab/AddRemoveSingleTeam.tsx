import React, { Component } from "react";
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

interface AddRemoveSingleTeamState {
  teamTypeaheadOptions: string[];
  selectedTeamKey: string;
  addButtonClass: string;
  removeButtonClass: string;
}

class AddRemoveSingleTeam extends Component<
  AddRemoveSingleTeamProps,
  AddRemoveSingleTeamState
> {
  private teamTypeahead: any = null;

  constructor(props: AddRemoveSingleTeamProps) {
    super(props);
    this.state = {
      teamTypeaheadOptions: [],
      selectedTeamKey: "",
      addButtonClass: "btn-primary",
      removeButtonClass: "btn-primary",
    };
    this.addSingleTeam = this.addSingleTeam.bind(this);
    this.removeSingleTeam = this.removeSingleTeam.bind(this);
    this.onTeamSelectionChanged = this.onTeamSelectionChanged.bind(this);
  }

  async componentDidMount(): Promise<void> {
    // Load team typeahead data
    const resp = await fetch("/_/typeahead/teams-all");
    const json: string[] = await resp.json();
    this.setState({ teamTypeaheadOptions: json });
  }

  UNSAFE_componentWillReceiveProps(nextProps: AddRemoveSingleTeamProps): void {
    if (!nextProps.hasFetchedTeams) {
      this.setState({
        addButtonClass: "btn-primary",
        removeButtonClass: "btn-primary",
      });
    }
  }

  onTeamSelectionChanged(selected: any[]): void {
    if (selected && selected.length > 0) {
      const teamValue = typeof selected[0] === 'string' ? selected[0] : String(selected[0]);
      const teamNumber = teamValue.split("|")[0].trim();
      this.setState({ selectedTeamKey: `frc${teamNumber}` });
    } else {
      this.setState({ selectedTeamKey: "" });
    }
  }

  addSingleTeam(): void {
    if (!this.props.hasFetchedTeams) {
      this.props.showErrorMessage(
        "Please fetch teams before modification to ensure up to date data"
      );
      return;
    }

    const existingTeamKeys = this.props.currentTeams.map((team) => team.key);
    const keyIndex = existingTeamKeys.indexOf(this.state.selectedTeamKey);
    if (keyIndex >= 0) {
      this.props.showErrorMessage(
        `Team ${this.state.selectedTeamKey} is already attending ${this.props.selectedEvent}. Re-fetch the team list if you know this is wrong.`
      );
      return;
    }

    existingTeamKeys.push(this.state.selectedTeamKey);
    this.setState({ addButtonClass: "btn-warning" });
    this.props.updateTeamList(
      existingTeamKeys,
      () => {
        this.setState({ addButtonClass: "btn-success" });
        this.teamTypeahead?.clear();
        if (this.props.clearTeams) {
          this.props.clearTeams();
        }
      },
      (error: string) => this.props.showErrorMessage(`${error}`)
    );
  }

  removeSingleTeam(): void {
    if (!this.props.hasFetchedTeams) {
      this.props.showErrorMessage(
        "Please fetch teams before modification to ensure up to date data"
      );
      return;
    }

    const existingTeamKeys = this.props.currentTeams.map((team) => team.key);
    const keyIndex = existingTeamKeys.indexOf(this.state.selectedTeamKey);
    if (keyIndex < 0) {
      this.props.showErrorMessage(
        `Team ${this.state.selectedTeamKey} is already not attending ${this.props.selectedEvent}. Re-fetch the team list if you know this is wrong.`
      );
      return;
    }

    existingTeamKeys.splice(keyIndex, 1);
    this.setState({ removeButtonClass: "btn-warning" });
    this.props.updateTeamList(
      existingTeamKeys,
      () => {
        this.setState({ removeButtonClass: "btn-success" });
        this.teamTypeahead?.clear();
        if (this.props.clearTeams) {
          this.props.clearTeams();
        }
      },
      (error: string) => this.props.showErrorMessage(`${error}`)
    );
  }

  render(): React.ReactNode {
    return (
      <div>
        <h4>Add/Remove Single Team</h4>
        {this.props.selectedEvent && !this.props.hasFetchedTeams && (
          <p>
            <em>Note:</em> Please fetch the current team list before adding or
            removing a team
          </p>
        )}
        <Typeahead
          ref={(typeahead) => {
            this.teamTypeahead = typeahead;
          }}
          id="teamTypeahead"
          placeholder="Enter team name or number..."
          options={this.state.teamTypeaheadOptions}
          onChange={this.onTeamSelectionChanged}
          disabled={!this.props.selectedEvent}
        />
        <button
          className={`btn ${this.state.addButtonClass}`}
          onClick={this.addSingleTeam}
          disabled={
            !this.props.selectedEvent ||
            !this.props.hasFetchedTeams ||
            !this.state.selectedTeamKey
          }
        >
          Add Team
        </button>
        <button
          className={`btn ${this.state.removeButtonClass}`}
          onClick={this.removeSingleTeam}
          disabled={
            !this.props.selectedEvent ||
            !this.props.hasFetchedTeams ||
            !this.state.selectedTeamKey
          }
        >
          Remove Team
        </button>
      </div>
    );
  }
}

export default AddRemoveSingleTeam;
