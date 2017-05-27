import React, { Component } from 'react'
import PropTypes from 'prop-types'

class EventWizardTabFrame extends Component {
  render() {
    return (
      <div>
        <div className="row">
          <div className="col-sm-12">
            <ul className="nav nav-tabs">
              <li><a href="#teams" data-toggle="tab">Manual Teams</a></li>
              <li><a href="#fms-teams" data-toggle="tab">FMS Teams</a></li>
              <li><a href="#schedule" data-toggle="tab">FMS Schedule Import</a></li>
              <li><a href="#matches" data-toggle="tab">Match Play</a></li>
              <li><a href="#results" data-toggle="tab">FMS Match Import</a></li>
              <li><a href="#rankings" data-toggle="tab">FMS Rankings Import</a></li>
              <li><a href="#alliances" data-toggle="tab">Alliance Selection</a></li>
            </ul>
          </div>
        </div>
        <div className="tab-content row">
          <div className="tab-pane" id="teams">
          </div>
          <div className="tab-pane" id="fms-teams">
          </div>
          <div className="tab-pane" id="schedule">
          </div>
          <div className="tab-pane" id="matches">
          </div>
          <div className="tab-pane" id="results">
          </div>
          <div className="tab-pane" id="rankings">
          </div>
          <div className="tab-pane" id="alliances">
          </div>
      </div>
        </div>
    )
  }
}

export default EventWizardTabFrame