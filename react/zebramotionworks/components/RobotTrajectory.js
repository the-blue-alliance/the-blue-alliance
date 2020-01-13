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
    const { teamData, startTime, endTime, color, indicatorAtStart } = this.props

    // Find first non-null entry
    let x = null
    let y = null
    if (indicatorAtStart) {
      for (let i = startTime; i <= endTime; i++) {
        x = teamData.xs[i]
        y = teamData.ys[i]
        if (x !== null && y !== null) {
          break
        }
      }
    } else {
      for (let i = endTime; i >= startTime; i--) {
        x = teamData.xs[i]
        y = teamData.ys[i]
        if (x !== null && y !== null) {
          break
        }
      }
    }

    return (
      <g>
        <path
          d={this.generatePath(teamData, startTime, endTime)}
          fill="none"
          stroke={color}
          strokeWidth={0.2}
        />
        {x && (
          <circle
            cx={x}
            cy={27 - y}
            r={1.3}
            fill="white"
            stroke={color}
            strokeWidth={0.2}
          />
        )}
        {x && (
          <text
            x={x}
            y={27 - y}
            fill="black"
            fontSize={1}
            dominantBaseline="middle"
            textAnchor="middle"
          >
            {teamData.team_key.substring(3)}
          </text>
        )}
      </g>
    )
  }
}

RobotTrajectory.propTypes = {
  teamData: PropTypes.object.isRequired,
  startTime: PropTypes.number.isRequired,
  endTime: PropTypes.number.isRequired,
  color: PropTypes.string.isRequired,
  indicatorAtStart: PropTypes.boolean,
}

export default RobotTrajectory
