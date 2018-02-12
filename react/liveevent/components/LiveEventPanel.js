import React, { PureComponent } from 'react'
import CurrentMatchDisplay from './CurrentMatchDisplay'
import LastMatchesTable from './LastMatchesTable'
import UpcomingMatchesTable from './UpcomingMatchesTable'

class LiveEventPanel extends PureComponent {
  render() {
    return (
      <div>
        <div className='col-md-3 text-center'>
          <h4>Last Matches</h4>
          <LastMatchesTable />
        </div>
        <div className='col-md-6 text-center'>
          <h4>Current Match: Quals 4</h4>
          <CurrentMatchDisplay />
        </div>
        <div className='col-md-3 text-center'>
          <h4>Upcoming Matches</h4>
          <UpcomingMatchesTable />
        </div>
        <div className='clearfix'></div>
      </div>
    )
  }
}

export default LiveEventPanel
