import React, { Component } from 'react'
import PropTypes from 'prop-types'
import TeamList from './TeamList'
import Dialog from 'react-bootstrap-dialog'
import { Typeahead } from 'react-bootstrap-typeahead'

class TeamListTab extends Component {

  constructor(props) {
    super(props)
    this.state = {
      teams: [],
      teamTypeaheadOptions: [],
      addSingleButtonStatus: 'btn-primary',
      removeSingleButtonStatus: 'btn-primary',
      addMultipleButtonStatus: 'btn-primary',
    }
    this.updateAttendingTeams = this.updateAttendingTeams.bind(this)
    this.addSingleTeam = this.addSingleTeam.bind(this)
    this.removeSingleTeam = this.removeSingleTeam.bind(this)
    this.addMultipleTeams = this.addMultipleTeams.bind(this)
  }

  componentWillReceiveProps(nextProps) {
    if (this.props.selectedEvent !== nextProps.selectedEvent) {
      this.setState({ teams: [] })
    }
  }

  componentDidMount() {
    // Load team typeahead data
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
      .then(function(response) {
        if (!response.ok) {
          throw new Error(response.statusText);
        }
        return response;
      })
      .then((response) => (response.json()))
      .then((data) => (data.sort(function(a, b){
        return a.team_number - b.team_number
      })))
      .then((data) => (this.setState({ teams: data })))
      .catch((error) => (this.refs.dialog.showAlert(`${error}`)))
  }

  addSingleTeam() {
    this.refs.dialog.showAlert('TODO: Implement API to add single team');
    this.setState({addSingleButtonStatus: 'btn-danger'});
  }

  removeSingleTeam() {
    this.refs.dialog.showAlert('TODO: Implement API to remove single team');
    this.setState({addSingleButtonStatus: 'btn-danger'});
  }

  addMultipleTeams() {
    if (!this.props.selectedEvent) {
      // No valid event
      return
    }

    this.setState({addMultipleButtonStatus: 'btn-warning'})
    this.props.makeTrustedRequest(
      '/api/trusted/v1/event/'+this.props.selectedEvent+'/team_list/update',
      '[]',
      (data) => this.setState({addMultipleButtonStatus: 'btn-success'}),
      (error) => (this.refs.dialog.showAlert(`${error}`))
    )
  }

  render() {
    return (
      <div className="tab-pane" id="teams">
        <Dialog ref="dialog" />
        <h3>Team List</h3>
        <div className="row">
          <div className="col-sm-6">
            <h4>Add/Remove Single Team</h4>
            <Typeahead
              placeholder="Enter team name or number..."
              options={this.state.teamTypeaheadOptions}
            />
            <button className={`btn ${this.state.addSingleButtonStatus}`} onClick={this.addSingleTeam} disabled>
              Add Team
            </button>
            <button className={`btn ${this.state.removeSingleButtonStatus}`} onClick={this.removeSingleTeam} disabled>
              Remove Team
            </button>

            <hr />
            <h4>Add Multiple Teams</h4>
            <p>Enter a list of team numbers, one per line. This will <em>overwrite</em> all existing teams for this event.</p>
            <textarea className="form-control" id="team_list" />
            <button className={`btn ${this.state.addMultipleButtonStatus}`} onClick={this.addMultipleTeams}>
              Overwrite Teams
            </button>

            <hr />
            <h4>Import FMS Report</h4>
          </div>
          <div className="col-sm-6">
            <h4>Currently Attending Teams</h4>
            <button className="btn btn-info" onClick={this.updateAttendingTeams}>
              Fetch Teams
            </button>
            <TeamList teams={this.state.teams} />

          </div>
        </div>
      </div>
    )
  }
}

TeamListTab.propTypes = {
  selectedEvent: PropTypes.string,
  makeTrustedRequest: PropTypes.func.isRequired,
}

export default TeamListTab
