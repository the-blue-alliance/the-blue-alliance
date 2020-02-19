import React from 'react'

import PropTypes from 'prop-types'
import h337 from 'heatmap.js'

const WIDTH = 54
const HEIGHT = 27
const GRID_SCALE = 2

class HeatmapVisualizer extends React.Component {
  constructor(props) {
    super(props)
    const { data } = props

    this.state = { activeCount: 0 }
    // Default teams as inactive
    data.alliances.red.forEach((team) => {
      this.state[team.team_key] = false
    })
    data.alliances.blue.forEach((team) => {
      this.state[team.team_key] = false
    })
  }

  componentDidMount() {
    const cfg = {
      container: this.ref,
    }
    this.heatmapInstance = h337.create(cfg)
    this.setData()
  }

  componentDidUpdate() {
    this.setData()
  }

  setData() {
    const { data } = this.props

    const gridWidth = WIDTH * GRID_SCALE
    const gridHeight = HEIGHT * GRID_SCALE
    const grid = new Array(gridWidth + 1)
    for (let i = 0; i < gridWidth + 1; i++) {
      grid[i] = new Array(gridHeight + 1).fill(0)
    }

    const dataLen = data.times.length

    const alliances = ['red', 'blue']
    alliances.forEach((color) => {
      data.alliances[color].forEach(({ team_key: teamKey, xs, ys }) => {
        if (this.state.activeCount === 0 || this.state[teamKey]) {
          for (let i = 0; i < dataLen; i++) {
            const x = xs[i]
            const y = ys[i]
            if (x !== null && y !== null) {
              grid[Math.floor(x * GRID_SCALE)][Math.floor(y * GRID_SCALE)] += 1
            }
          }
        }
      })
    })

    const xScale = this.ref.offsetWidth / WIDTH
    const yScale = this.ref.offsetHeight / HEIGHT
    const heatmapData = []
    let max = 0
    for (let x = 0; x < WIDTH * GRID_SCALE; x++) {
      for (let y = 0; y < HEIGHT * GRID_SCALE; y++) {
        const value = grid[x][y]
        max = Math.max(max, value)
        if (value > 0) {
          const scaledY = y / GRID_SCALE
          heatmapData.push({
            x: (x / GRID_SCALE) * xScale,
            y: (27 - scaledY) * yScale,
            value,
          })
        }
      }
    }

    this.heatmapInstance.setData({
      min: 0,
      max,
      data: heatmapData,
    })
  }

  render() {
    const { fieldImg, data } = this.props

    return (
      <div>
        <div ref={(e) => (this.ref = e)}>
          <svg
            viewBox="0 0 54 27"
            style={{
              background: `url(${fieldImg}) no-repeat center center`,
              backgroundSize: 'cover',
            }}
          />
        </div>

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
                    activeCount: state[team.team_key]
                      ? state.activeCount - 1
                      : state.activeCount + 1,
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
                    activeCount: state[team.team_key]
                      ? state.activeCount - 1
                      : state.activeCount + 1,
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
  fieldImg: PropTypes.string.isRequired,
  data: PropTypes.object.isRequired,
}

export default HeatmapVisualizer
