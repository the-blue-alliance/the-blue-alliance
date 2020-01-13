import React from 'react'
import PropTypes from 'prop-types'

const pathTimeLength = 50

class ZebraMotionWorksVisualizer extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      autoPlay: false,
      playStartTime: null,
      playOffset: null,
      curTime: 0,
      maxTime: props.data.times.length,
    }
  }

  componentDidMount() {
    this.displayFrame()
  }

  displayFrame = () => {
    const { autoPlay, playStartTime, playOffset } = this.state
    if (autoPlay) {
      const elapsedTime = Date.now() - playStartTime
      this.setState((state) => ({
        curTime: (Math.round(elapsedTime / 10) + playOffset) % state.maxTime,
      }))
    }
    requestAnimationFrame(() => this.displayFrame())
  }

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

  handlePlayPause = () => {
    this.setState((state) => ({
      autoPlay: !state.autoPlay,
      playStartTime: state.autoPlay ? null : Date.now(),
      playOffset: state.autoPlay ? null : state.curTime,
    }))
  }

  handleSliderChange = (event) => {
    if (!this.state.autoPlay) {
      this.setState({ curTime: parseInt(event.target.value, 10) })
    }
  }

  render() {
    const { data } = this.props
    const { autoPlay, curTime: startTime, maxTime } = this.state
    const endTime = startTime + pathTimeLength

    return (
      <div>
        <svg
          viewBox="0 0 54 27"
          style={{
            background: 'url(/images/2019_field.png) no-repeat center center',
            backgroundSize: 'cover',
          }}
        >
          <path
            d={this.generatePath(data.red[0], startTime, endTime)}
            fill="none"
            stroke="#FF0000"
            strokeWidth={0.2}
          />
          <path
            d={this.generatePath(data.red[1], startTime, endTime)}
            fill="none"
            stroke="#800000"
            strokeWidth={0.2}
          />
          <path
            d={this.generatePath(data.red[2], startTime, endTime)}
            fill="none"
            stroke="#FF8080"
            strokeWidth={0.2}
          />
          <path
            d={this.generatePath(data.blue[0], startTime, endTime)}
            fill="none"
            stroke="#0000FF"
            strokeWidth={0.2}
          />
          <path
            d={this.generatePath(data.blue[1], startTime, endTime)}
            fill="none"
            stroke="#000080"
            strokeWidth={0.2}
          />
          <path
            d={this.generatePath(data.blue[2], startTime, endTime)}
            fill="none"
            stroke="#8080FF"
            strokeWidth={0.2}
          />
        </svg>
        <div style={{ width: '100%', display: 'flex' }}>
          <button
            className="btn btn-tiny"
            style={{ marginRight: 8 }}
            onClick={this.handlePlayPause}
          >
            {autoPlay ? (
              <span className="glyphicon glyphicon-pause" />
            ) : (
              <span className="glyphicon glyphicon-play" />
            )}
          </button>
          <input
            type="range"
            min={0}
            max={maxTime - pathTimeLength}
            step={1}
            value={startTime}
            onChange={this.handleSliderChange}
          />
        </div>
      </div>
    )
  }
}

ZebraMotionWorksVisualizer.propTypes = {
  data: PropTypes.object.isRequired,
}

export default ZebraMotionWorksVisualizer
