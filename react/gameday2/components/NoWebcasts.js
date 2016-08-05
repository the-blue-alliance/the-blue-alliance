import React from 'react'

const NoWebcasts = React.createClass({
  render: function() {
    return (
      <div className='no-webcasts-container'>
        <h1>No webcasts found</h1>
        <p>Looks like there aren't any events with webcasts this week. Check on The Blue Alliance for upcoming events!</p>
        <a className="btn btn-default" href="https://thebluealliance.com">Go to The Blue Alliance</a>
      </div>
    )
  }
})

export default NoWebcasts
