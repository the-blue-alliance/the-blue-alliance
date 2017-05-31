import React, { Component } from 'react'
import PropTypes from 'prop-types'
import TeamItem from './TeamItem'
import Dialog from 'react-bootstrap-dialog'
import { Typeahead } from 'react-bootstrap-typeahead'

class TeamListTab extends Component {

  static checkStatus(response) {
    if (response.status >= 200 && response.status < 300) {
      return response
    }

    const error = new Error(response.statusText)
    error.response = response
    throw error
  }

  constructor(props) {
    super(props)
    this.state = {
      teams: [],
      teamTypeaheadOptions: [],
    }
    this.updateAttendingTeams = this.updateAttendingTeams.bind(this)
  }

  componentWillReceiveProps(nextProps) {
    if (this.props.selectedEvent !== nextProps.selectedEvent) {
      this.setState({ teams: [] })
    }
  }

  componentDidMount() {
    fetch('/_/typeahead/teams-all')
      .then(resp => resp.json())
      .then(json => this.setState({teamTypeaheadOptions: json}))
  }

  updateAttendingTeams() {
    if (!this.props.selectedEvent) {
      // No valid event
      return
    }

    fetch(`/api/v3/event/${this.props.selectedEvent}/teams`, {
      credentials: 'same-origin',
    })
      .then(this.checkStatus)
      .then((response) => (response.json()))
      .then((data) => (data.sort(function(a, b){
        return a.team_number - b.team_number
      })))
      .then((data) => (this.setState({ teams: data })))
      .catch((error) => (this.refs.dialog.showAlert(`Network Error: ${error}`)))
  }

  render() {
    return (
      <div className="tab-pane" id="teams">
        <Dialog ref="dialog" />
        <h3>Team List</h3>
        <div className="row">
          <div className="col-sm-6">
            <h4>Add Single Team</h4>
            <Typeahead
              placeholder="Enter team name or number..."
              options={this.state.teamTypeaheadOptions}
            />
            <h4>Add Multiple Teams</h4>
            <h4>Import FMS Report</h4>
          </div>
          <div className="col-sm-6">
            <h4>Attending Teams</h4>
            <button className="btn btn-info" onClick={this.updateAttendingTeams}>
              Fetch Teams
            </button>
            {this.state.teams.length > 0 &&
              <p>
                {this.state.teams.length} teams attending
              </p>
            }
            <ul>
              {this.state.teams.map((team) =>
                <TeamItem
                  key={team.key}
                  team_number={team.team_number}
                  nickname={team.nickname}
                />
              )}
            </ul>

          </div>
        </div>
      </div>
    )
  }
}

TeamListTab.propTypes = {
  selectedEvent: PropTypes.string,
}

export default TeamListTab
