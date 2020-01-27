import React from 'react'
import PropTypes from 'prop-types'

const WIDTH = 54
const HEIGHT = 27
const GRID_SCALE = 2

function createColor(perc) {
  let r = 0
  let g = 0
  if (perc < 50) {
    r = 255
    g = Math.round(5.1 * perc)
  } else {
    g = 255
    r = Math.round(510 - 5.1 * perc)
  }
  let h = r * 0x10000
  h += g * 0x100
  return `#${`000000${h.toString(16)}`.slice(-6)}`
}

class HeatmapVisualizer extends React.Component {
  constructor(props) {
    super(props)
    const { data } = props
    console.log(data)

    this.state = {}
    // Default teams as active
    data.alliances.red.forEach((team) => {
      this.state[team.team_key] = true
    })
    data.alliances.blue.forEach((team) => {
      this.state[team.team_key] = true
    })
  }

  render() {
    const { data } = this.props

    console.time('!')
    const grid = new Array(WIDTH * GRID_SCALE)
    for (let i = 0; i < WIDTH * GRID_SCALE; i++) {
      grid[i] = new Array(HEIGHT * GRID_SCALE).fill(0)
    }
    console.timeEnd('!')

    console.time('XX')
    const dataLength = data.times.length
    data.alliances.red.forEach((team) => {
      if (this.state[team.team_key]) {
        for (let i = 0; i < dataLength; i++) {
          const x = team.xs[i]
          const y = team.ys[i]
          grid[Math.floor(x * GRID_SCALE)][Math.floor(y * GRID_SCALE)] += 1
        }
      }
    })
    data.alliances.blue.forEach((team) => {
      if (this.state[team.team_key]) {
        for (let i = 0; i < dataLength; i++) {
          const x = team.xs[i]
          const y = team.ys[i]
          grid[Math.floor(x * GRID_SCALE)][Math.floor(y * GRID_SCALE)] += 1
        }
      }
    })
    console.timeEnd('XX')
    console.log(grid)

    console.time('A')
    const svgGrid = []
    for (let i = 0; i < WIDTH * GRID_SCALE; i++) {
      for (let j = 0; j < HEIGHT * GRID_SCALE; j++) {
        const value = (100 * grid[i][j]) / 10
        if (value !== 0) {
          svgGrid.push(
            <rect
              x={i * 0.5}
              y={j * 0.5}
              width="0.5"
              height="0.5"
              fill={createColor(100 - value)}
              fillOpacity="0.5"
            />
          )
        }
      }
    }
    console.timeEnd('A')

    return (
      <div>
        <svg
          viewBox="0 0 54 27"
          style={{
            background: 'url(/images/2019_field.png) no-repeat center center',
            backgroundSize: 'cover',
          }}
        >
          <g>{svgGrid}</g>
        </svg>

        <div
          style={{
            display: 'flex',
            width: '100%',
            justifyContent: 'space-around',
          }}
        >
          <div
            className="btn-group"
            role="group"
            style={{ display: 'flex', marginRight: 8 }}
          >
            {data.alliances.red.map((team) => (
              <button
                key={team.team_key}
                type="button"
                className={`btn btn-tiny${
                  this.state[team.team_key] ? ' active' : ''
                }`}
                style={{ backgroundColor: '#ffdddd' }}
                onClick={() =>
                  this.setState((state) => ({
                    [team.team_key]: !state[team.team_key],
                  }))
                }
              >
                {team.team_key.substring(3)}
              </button>
            ))}
          </div>
          <div
            className="btn-group"
            role="group"
            style={{ display: 'flex', marginRight: 8 }}
          >
            {data.alliances.blue.map((team) => (
              <button
                key={team.team_key}
                type="button"
                className={`btn btn-tiny${
                  this.state[team.team_key] ? ' active' : ''
                }`}
                style={{ backgroundColor: '#ddddff' }}
                onClick={() =>
                  this.setState((state) => ({
                    [team.team_key]: !state[team.team_key],
                  }))
                }
              >
                {team.team_key.substring(3)}
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }
}

HeatmapVisualizer.propTypes = {
  data: PropTypes.object.isRequired,
}

export default HeatmapVisualizer
