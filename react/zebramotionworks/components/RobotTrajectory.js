import React from 'react'
import PropTypes from 'prop-types'

class RobotTrajectory extends React.PureComponent {
  generatePath = (teamData, startTime, endTime) => {
    let path = ''
    let first = true
    for (let i = startTime; i < Math.min(teamData.xs.length, endTime); i++) {
      if (teamData.xs[i] !== null && teamData.ys[i] !== null) {
        if (first) {
          first = false
          path = `M ${teamData.xs[i]} ${27 - teamData.ys[i]}`
        }
        path += ` L ${teamData.xs[i]} ${27 - teamData.ys[i]}`
      }
    }
    return path
  }

  render() {
    const { teamData, startTime, endTime, color } = this.props

    return (
      <path
        d={this.generatePath(teamData, startTime, endTime)}
        fill="none"
        stroke={color}
        strokeWidth={0.2}
      />
    )
  }
}

RobotTrajectory.propTypes = {
  teamData: PropTypes.object.isRequired,
  startTime: PropTypes.number.isRequired,
  endTime: PropTypes.number.isRequired,
  color: PropTypes.string.isRequired,
}

export default RobotTrajectory
