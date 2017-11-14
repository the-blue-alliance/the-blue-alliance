
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
    }

    this.onNextFromTeamChange = this.onNextFromTeamChange.bind(this)
    this.onNextToTeamChange = this.onNextToTeamChange.bind(this)
    this.onAddTeamMapClick = this.onAddTeamMapClick.bind(this)
  }

  onNextFromTeamChange(event) {
    this.setState({ nextFromTeam: event.target.value })
  }

  onNextToTeamChange(event) {
    this.setState({ nextToTeam: event.target.value })
  }

  onAddTeamMapClick() {
    this.props.addTeamMap(`frc${this.state.nextFromTeam.toUpperCase()}`, `frc${this.state.nextToTeam.toUpperCase()}`)
    this.setState({ nextFromTeam: '', nextToTeam: '' })
  }

  render() {
    let teamMappingsList = null
    if (this.props.eventInfo && Object.keys(this.props.eventInfo.remap_teams).length > 0) {
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

          <div className="input-group">
            <input
              className="form-control"
              type="text"
              placeholder="9254"
              disabled={this.props.eventInfo === null}
              onChange={this.onNextFromTeamChange}
              value={this.state.nextFromTeam}
            />
            <span className="input-group-addon"><span className="glyphicon glyphicon-arrow-right" aria-hidden="true"></span></span>
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
                disabled={this.props.eventInfo === null}
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
