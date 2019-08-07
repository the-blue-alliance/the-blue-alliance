
import React, { Component } from 'react'
import PropTypes from 'prop-types'

import TeamMappingsList from './TeamMappingsList'
import EVENT_SHAPE from '../../constants/ApiEvent'

class AddRemoveTeamMap extends Component {
  constructor(props) {
    super(props)
    this.state = {
      nextFromTeam: '',
      nextToTeam: '',
      fromError: false,
      toError: false,
    }

    this.onNextFromTeamChange = this.onNextFromTeamChange.bind(this)
    this.onNextToTeamChange = this.onNextToTeamChange.bind(this)
    this.onAddTeamMapClick = this.onAddTeamMapClick.bind(this)
  }

  onNextFromTeamChange(event) {
    const match = event.target.value.match(/\d+/)
    this.setState({ nextFromTeam: event.target.value, fromError: !match || match[0] !== event.target.value })
  }

  onNextToTeamChange(event) {
    const match = event.target.value.match(/\d+[b-zB-Z]?/)
    this.setState({ nextToTeam: event.target.value, toError: !match || match[0] !== event.target.value })
  }

  onAddTeamMapClick() {
    this.props.addTeamMap(`frc${this.state.nextFromTeam.toUpperCase()}`, `frc${this.state.nextToTeam.toUpperCase()}`)
    this.setState({ nextFromTeam: '', nextToTeam: '', fromError: false, toError: false })
  }

  render() {
    let teamMappingsList = null
    if (this.props.eventInfo && this.props.eventInfo.remap_teams && Object.keys(this.props.eventInfo.remap_teams).length > 0) {
      teamMappingsList =
        (<TeamMappingsList
          teamMappings={this.props.eventInfo.remap_teams}
          removeTeamMap={this.props.removeTeamMap}
        />)
    } else {
      teamMappingsList = (<p>No team mappings found</p>)
    }

    return (
      <div className="form-group">
        <label htmlFor="team_mappings_list" className="col-sm-2 control-label">
          Team Mappings
          <br />
          <small>Note: Removing a mapping will not unmap existing data!</small>
        </label>
        <div className="col-sm-10" id="team_mappings_list">
          {teamMappingsList}

          <div className={this.state.fromError || this.state.toError ? 'input-group has-error' : 'input-group'}>
            <input
              className="form-control"
              type="text"
              placeholder="9254"
              disabled={this.props.eventInfo === null}
              onChange={this.onNextFromTeamChange}
              value={this.state.nextFromTeam}
            />
            <span className="input-group-addon"><span className="glyphicon glyphicon-arrow-right" aria-hidden="true" /></span>
            <input
              className="form-control"
              type="text"
              placeholder="254B"
              disabled={this.props.eventInfo === null}
              onChange={this.onNextToTeamChange}
              value={this.state.nextToTeam}
            />
            <span className="input-group-btn">
              <button
                className="btn btn-info"
                onClick={this.onAddTeamMapClick}
                disabled={this.props.eventInfo === null || this.state.fromError || this.state.toError}
              >
                Add Mapping
              </button>
            </span>
          </div>
        </div>
      </div>
    )
  }
}

AddRemoveTeamMap.propTypes = {
  eventInfo: PropTypes.shape(EVENT_SHAPE),
  addTeamMap: PropTypes.func.isRequired,
  removeTeamMap: PropTypes.func.isRequired,
}

export default AddRemoveTeamMap
