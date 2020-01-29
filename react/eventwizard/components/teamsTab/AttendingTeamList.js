import React, { Component } from 'react'
import PropTypes from 'prop-types'

import TEAM_SHAPE from '../../constants/ApiTeam'
import ensureRequestSuccess from '../../net/EnsureRequestSuccess'
import TeamList from './TeamList'

class AttendingTeamList extends Component {
  constructor(props) {
    super(props)
    this.state = {
      buttonClass: 'btn-info',
    }

    this.updateAttendingTeams = this.updateAttendingTeams.bind(this)
  }

  componentWillReceiveProps(nextProps) {
    if (!nextProps.hasFetchedTeams) {
      this.setState({ buttonClass: 'btn-info' })
    }
  }

  updateAttendingTeams() {
    if (!this.props.selectedEvent) {
      // No valid event
      this.props.showErrorMessage('Please select an event before fetching teams')
      return
    }

    this.setState({ buttonClass: 'btn-warning' })
    fetch(`/api/v3/event/${this.props.selectedEvent}/teams/simple`, {
      credentials: 'same-origin',
    })
      .then(ensureRequestSuccess)
      .then((response) => (response.json()))
      .then((data) => (data.sort((a, b) => a.team_number - b.team_number)))
      .then((data) => (this.props.updateTeams(data)))
      .then(() => (this.setState({ buttonClass: 'btn-success' })))
      .catch((error) => {
        this.props.showErrorMessage(`${error}`)
        this.setState({ buttonClass: 'btn-danger' })
      }
      )
  }

  render() {
    let renderedTeams
    if (this.props.hasFetchedTeams && this.props.teams.length === 0) {
      renderedTeams = <p>No teams found</p>
    } else {
      renderedTeams = <TeamList teams={this.props.teams} />
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
    )
  }
}

AttendingTeamList.propTypes = {
  selectedEvent: PropTypes.string,
  hasFetchedTeams: PropTypes.bool.isRequired,
  teams: PropTypes.arrayOf(PropTypes.shape(TEAM_SHAPE)).isRequired,
  updateTeams: PropTypes.func.isRequired,
  showErrorMessage: PropTypes.func.isRequired,
}

export default AttendingTeamList
