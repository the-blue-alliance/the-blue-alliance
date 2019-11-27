import React, { Component } from 'react'
import PropTypes from 'prop-types'
import { Typeahead } from 'react-bootstrap-typeahead'

import TEAM_SHAPE from '../../constants/ApiTeam'

class AddRemoveSingleTeam extends Component {
  constructor(props) {
    super(props)
    this.state = {
      teamTypeaheadOptions: [],
      selectedTeamKey: '',
      addButtonClass: 'btn-primary',
      removeButtonClass: 'btn-primary',
    }
    this.addSingleTeam = this.addSingleTeam.bind(this)
    this.removeSingleTeam = this.removeSingleTeam.bind(this)
    this.onTeamSelectionChanged = this.onTeamSelectionChanged.bind(this)
  }

  componentDidMount() {
    // Load team typeahead data
    fetch('/_/typeahead/teams-all')
      .then((resp) => resp.json())
      .then((json) => this.setState({ teamTypeaheadOptions: json }))
  }

  componentWillReceiveProps(nextProps) {
    if (!nextProps.hasFetchedTeams) {
      this.setState({ addButtonClass: 'btn-primary', removeButtonClass: 'btn-primary' })
    }
  }

  onTeamSelectionChanged(selected) {
    if (selected && selected.length > 0) {
      const teamNumber = selected[0].split('|')[0].trim()
      this.setState({ selectedTeamKey: `frc${teamNumber}` })
    } else {
      this.setState({ selectedTeamKey: '' })
    }
  }

  addSingleTeam() {
    if (!this.props.hasFetchedTeams) {
      this.props.showErrorMessage('Please fetch teams before modification to ensure up to date data')
      return
    }

    const existingTeamKeys = this.props.currentTeams.map((team) => (team.key))
    const keyIndex = existingTeamKeys.indexOf(this.state.selectedTeamKey)
    if (keyIndex >= 0) {
      this.props.showErrorMessage(`Team ${this.state.selectedTeamKey} is already attending ${this.props.selectedEvent}. Re-fetch the team list if you know this is wrong.`)
      return
    }

    existingTeamKeys.push(this.state.selectedTeamKey)
    this.setState({ addButtonClass: 'btn-warning' })
    this.props.updateTeamList(
      existingTeamKeys,
      () => {
        this.setState({ addButtonClass: 'btn-success' })
        this.teamTypeahead.getInstance().clear()
        this.props.clearTeams()
      },
      (error) => (this.props.showErrorMessage(`${error}`))
    )
  }

  removeSingleTeam() {
    if (!this.props.hasFetchedTeams) {
      this.props.showErrorMessage('Please fetch teams before modification to ensure up to date data')
      return
    }

    const existingTeamKeys = this.props.currentTeams.map((team) => (team.key))
    const keyIndex = existingTeamKeys.indexOf(this.state.selectedTeamKey)
    if (keyIndex < 0) {
      this.props.showErrorMessage(`Team ${this.state.selectedTeamKey} is already not attending ${this.props.selectedEvent}. Re-fetch the team list if you know this is wrong.`)
      return
    }

    existingTeamKeys.splice(keyIndex, 1)
    this.setState({ removeButtonClass: 'btn-warning' })
    this.props.updateTeamList(
      existingTeamKeys,
      () => {
        this.setState({ removeButtonClass: 'btn-success' })
        this.teamTypeahead.getInstance().clear()
        this.props.clearTeams()
      },
      (error) => (this.props.showErrorMessage(`${error}`))
    )
  }

  render() {
    return (
      <div>
        <h4>Add/Remove Single Team</h4>
        {this.props.selectedEvent && !this.props.hasFetchedTeams &&
          <p><em>Note:</em> Please fetch the current team list before adding or removing a team</p>
        }
        <Typeahead
          ref={(typeahead) => { this.teamTypeahead = typeahead }}
          placeholder="Enter team name or number..."
          options={this.state.teamTypeaheadOptions}
          onChange={this.onTeamSelectionChanged}
          disabled={!this.props.selectedEvent}
        />
        <button
          className={`btn ${this.state.addButtonClass}`}
          onClick={this.addSingleTeam}
          disabled={!this.props.selectedEvent || !this.props.hasFetchedTeams || !this.state.selectedTeamKey}
        >
          Add Team
        </button>
        <button
          className={`btn ${this.state.removeButtonClass}`}
          onClick={this.removeSingleTeam}
          disabled={!this.props.selectedEvent || !this.props.hasFetchedTeams || !this.state.selectedTeamKey}
        >
          Remove Team
        </button>
      </div>
    )
  }
}

AddRemoveSingleTeam.propTypes = {
  selectedEvent: PropTypes.string,
  updateTeamList: PropTypes.func.isRequired,
  hasFetchedTeams: PropTypes.bool.isRequired,
  currentTeams: PropTypes.arrayOf(PropTypes.shape(TEAM_SHAPE)).isRequired,
  clearTeams: PropTypes.func,
  showErrorMessage: PropTypes.func.isRequired,
}

export default AddRemoveSingleTeam
