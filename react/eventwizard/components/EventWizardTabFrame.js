import React from 'react'
import EventInfoContainer from '../containers/EventInfoContainer'
import TeamListContainer from '../containers/TeamListContainer'

const EventWizardTabFrame = () => (
  <div>
    <div className="row">
      <div className="col-sm-12">
        <ul className="nav nav-tabs">
          <li><a href="#info" data-toggle="tab">Event Info</a></li>
          <li><a href="#teams" data-toggle="tab">Teams</a></li>
          <li><a href="#schedule" data-toggle="tab">FMS Schedule Import</a></li>
          <li><a href="#matches" data-toggle="tab">Match Play</a></li>
          <li><a href="#results" data-toggle="tab">FMS Match Import</a></li>
          <li><a href="#rankings" data-toggle="tab">FMS Rankings Import</a></li>
          <li><a href="#alliances" data-toggle="tab">Alliance Selection</a></li>
        </ul>
      </div>
    </div>
    <div className="tab-content row">
      <EventInfoContainer />
      <TeamListContainer />
      <div className="tab-pane" id="schedule">
        <h3>FMS Schedule</h3>
      </div>
      <div className="tab-pane" id="matches">
        <h3>Match Play</h3>
      </div>
      <div className="tab-pane" id="results">
        <h3>FMS Matches</h3>
      </div>
      <div className="tab-pane" id="rankings">
        <h3>FMS Rankings</h3>
      </div>
      <div className="tab-pane" id="alliances">
        <h3>FMS Alliances</h3>
      </div>
    </div>
  </div>
)

export default EventWizardTabFrame
