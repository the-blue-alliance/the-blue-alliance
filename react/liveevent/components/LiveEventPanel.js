import React from 'react'
import CurrentMatchDisplay from './CurrentMatchDisplay'
import LastMatchesTable from './LastMatchesTable'
import UpcomingMatchesTable from './UpcomingMatchesTable'

const LiveEventPanel = () => (
  <div>
    <div className="col-lg-3 text-center">
      <h4>Last Matches</h4>
      <LastMatchesTable />
    </div>
    <div className="col-lg-6 text-center">
      <h4>Current Match: Quals 4</h4>
      <CurrentMatchDisplay />
    </div>
    <div className="col-lg-3 text-center">
      <h4>Upcoming Matches</h4>
      <UpcomingMatchesTable />
    </div>
    <div className="clearfix" />
  </div>
)

export default LiveEventPanel
