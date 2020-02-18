import React from 'react'
import PropTypes from 'prop-types'

import RobotTrajectory from './RobotTrajectory'

const pathTimeLength = 50

class TrajectoryVisualizer extends React.Component {
  constructor(props) {
    super(props)
    this.state = {
      showAll: true,
      autoPlay: false,
      playSpeed: 2,
      curTime: 0,
      maxTime: props.data.times.length,
    }
  }

  componentDidMount() {
    this.displayFrame()
    this.lastFrameTime = null
  }

  componentWillUnmount() {
    if (this.raf) {
      cancelAnimationFrame(this.raf)
    }
  }

  getTruePlaybackSpeed = (playSpeed) => {
    switch (playSpeed) {
      case 2:
        return 5
      case 3:
        return 10
      default:
        return 1
    }
  }

  displayFrame = () => {
    const { autoPlay, playSpeed } = this.state
    if (autoPlay && this.lastFrameTime) {
      const elapsedTime = Date.now() - this.lastFrameTime
      this.lastFrameTime = Date.now()

      const timeDiff =
        (elapsedTime / 1000) * 10 * this.getTruePlaybackSpeed(playSpeed)
      this.setState((state) => ({
        curTime: (state.curTime + timeDiff) % state.maxTime,
      }))
    } else {
      this.lastFrameTime = Date.now()
    }
    this.raf = requestAnimationFrame(() => this.displayFrame())
  }

  handleShowEntireMatch = () => {
    this.setState({ showAll: true, autoPlay: false, curTime: 0 })
  }

  handlePlayPause = () => {
    this.setState((state) => ({
      showAll: false,
      autoPlay: !state.autoPlay,
    }))
  }

  handleSlowDown = () => {
    this.setState((state) => ({
      playSpeed: Math.max(1, state.playSpeed - 1),
    }))
  }

  handleSpeedUp = () => {
    this.setState((state) => ({
      playSpeed: Math.min(3, state.playSpeed + 1),
    }))
  }

  handleSliderChange = (event) => {
    this.setState({
      autoPlay: false,
      showAll: false,
      curTime: parseInt(event.target.value, 10),
    })
  }

  render() {
    const { fieldImg, data } = this.props
    const { showAll, autoPlay, playSpeed, curTime, maxTime } = this.state
    const startTime = showAll ? 0 : Math.max(curTime - pathTimeLength, 0)
    const endTime = showAll ? maxTime : curTime
    const mm = Math.floor(curTime / 10 / 60)
      .toString()
      .padStart(2, '0')
    const ss = Math.floor((curTime / 10) % 60)
      .toString()
      .padStart(2, '0')

    return (
      <div>
        <svg
          viewBox="0 0 54 27"
          style={{
            background: `url(${fieldImg}) no-repeat center center`,
            backgroundSize: 'cover',
          }}
        >
          <RobotTrajectory
            teamData={data.alliances.red[0]}
            startTime={startTime}
            endTime={endTime}
            color="#FF0000"
            indicatorAtStart={showAll}
          />
          <RobotTrajectory
            teamData={data.alliances.red[1]}
            startTime={startTime}
            endTime={endTime}
            color="#800000"
            indicatorAtStart={showAll}
          />
          <RobotTrajectory
            teamData={data.alliances.red[2]}
            startTime={startTime}
            endTime={endTime}
            color="#FF8080"
            indicatorAtStart={showAll}
          />
          <RobotTrajectory
            teamData={data.alliances.blue[0]}
            startTime={startTime}
            endTime={endTime}
            color="#0000FF"
            indicatorAtStart={showAll}
          />
          <RobotTrajectory
            teamData={data.alliances.blue[1]}
            startTime={startTime}
            endTime={endTime}
            color="#000080"
            indicatorAtStart={showAll}
          />
          <RobotTrajectory
            teamData={data.alliances.blue[2]}
            startTime={startTime}
            endTime={endTime}
            color="#8080FF"
            indicatorAtStart={showAll}
          />
        </svg>
        <div style={{ width: '100%', display: 'flex', alignItems: 'center' }}>
          <button
            className="btn btn-tiny"
            style={{ marginRight: 8 }}
            onClick={this.handleShowEntireMatch}
            disabled={showAll}
          >
            <span className="glyphicon glyphicon-eye-open" />
          </button>
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
          <div
            className="btn-group"
            role="group"
            style={{ display: 'flex', marginRight: 8 }}
          >
            <button
              type="button"
              className="btn btn-tiny"
              onClick={this.handleSlowDown}
              disabled={playSpeed === 1}
            >
              <span className="glyphicon glyphicon-backward" />
            </button>
            <button type="button" className="btn btn-tiny" disabled>
              {`${this.getTruePlaybackSpeed(playSpeed)}x`}
            </button>
            <button
              type="button"
              className="btn btn-tiny"
              onClick={this.handleSpeedUp}
              disabled={playSpeed === 3}
            >
              <span className="glyphicon glyphicon-forward" />
            </button>
          </div>
          <input
            type="range"
            min={0}
            max={maxTime}
            step={1}
            value={curTime}
            onChange={this.handleSliderChange}
          />
          <div style={{ marginLeft: 8 }}>{`${mm}:${ss}`}</div>
        </div>
      </div>
    )
  }
}

TrajectoryVisualizer.propTypes = {
  fieldImg: PropTypes.string.isRequired,

  data: PropTypes.object.isRequired,
}

export default TrajectoryVisualizer
