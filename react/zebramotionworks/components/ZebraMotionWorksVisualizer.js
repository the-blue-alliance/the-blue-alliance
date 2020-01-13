import React from 'react'
import PropTypes from 'prop-types'

import RobotTrajectory from './RobotTrajectory'

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
          <RobotTrajectory
            teamData={data.red[0]}
            startTime={startTime}
            endTime={endTime}
            color="#FF0000"
          />
          <RobotTrajectory
            teamData={data.red[1]}
            startTime={startTime}
            endTime={endTime}
            color="#800000"
          />
          <RobotTrajectory
            teamData={data.red[2]}
            startTime={startTime}
            endTime={endTime}
            color="#FF8080"
          />
          <RobotTrajectory
            teamData={data.blue[0]}
            startTime={startTime}
            endTime={endTime}
            color="#0000FF"
          />
          <RobotTrajectory
            teamData={data.blue[1]}
            startTime={startTime}
            endTime={endTime}
            color="#000080"
          />
          <RobotTrajectory
            teamData={data.blue[2]}
            startTime={startTime}
            endTime={endTime}
            color="#8080FF"
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
