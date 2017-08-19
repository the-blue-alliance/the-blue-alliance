import React, { Component } from 'react'
import PropTypes from 'prop-types'
import Dialog from 'react-bootstrap-dialog'

import AddRemoveSingleTeam from './AddRemoveSingleTeam'
import AddMultipleTeams from './AddMultipleTeams'
import AddTeamsFMSReport from './AddTeamsFMSReport'
import AttendingTeamList from './AttendingTeamList'

class TeamListTab extends Component {

  constructor(props) {
    super(props)
    this.state = {
      teams: [],
      hasFetchedTeams: false,
      addMultipleButtonStatus: 'btn-primary',
    }
    this.showError = this.showError.bind(this)
    this.updateTeams = this.updateTeams.bind(this)
    this.clearTeams = this.clearTeams.bind(this)
  }

  componentWillReceiveProps(nextProps) {
    if (this.props.selectedEvent !== nextProps.selectedEvent) {
      this.clearTeams()
    }
  }

  showError(errorMessage) {
    this.refs.dialog.showAlert(errorMessage)
  }

  updateTeams(teams) {
    this.setState({teams: teams, hasFetchedTeams: true})
  }

  clearTeams() {
    this.setState({teams: [], hasFetchedTeams: false})
  }

  render() {
    return (
      <div className="tab-pane" id="teams">
        <Dialog ref="dialog" />
        <h3>Team List</h3>
        <div className="row">
          <div className="col-sm-6">
            <AddRemoveSingleTeam
              selectedEvent={this.props.selectedEvent}
              makeTrustedRequest={this.props.makeTrustedRequest}
              showErrorMessage={this.showError}
              clearTeams={this.clearTeams}
            />
            <hr />

            <AddMultipleTeams
              selectedEvent={this.props.selectedEvent}
              makeTrustedRequest={this.props.makeTrustedRequest}
              showErrorMessage={this.showError}
              clearTeams={this.clearTeams}
            />
            <hr />

            <AddTeamsFMSReport
              selectedEvent={this.props.selectedEvent}
              makeTrustedRequest={this.props.makeTrustedRequest}
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
    )
  }
}

TeamListTab.propTypes = {
  selectedEvent: PropTypes.string,
  makeTrustedRequest: PropTypes.func.isRequired,
}

export default TeamListTab
