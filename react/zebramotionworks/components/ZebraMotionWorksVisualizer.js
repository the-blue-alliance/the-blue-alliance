import React from 'react'
import PropTypes from 'prop-types'
import TrajectoryVisualizer from './TrajectoryVisualizer'
import HeatmapVisualizer from './HeatmapVisualizer'

class ZebraMotionWorksVisualizer extends React.Component {
  state = {
    mode: 'traj',
  }

  handleTrajectoryClick = () => {
    this.setState({ mode: 'traj' })
  }

  handleHeatmapClick = () => {
    this.setState({ mode: 'heat' })
  }

  render() {
    const { data, year } = this.props
    const { mode } = this.state
    return (
      <div>
        <div className="row">
          <div className="col-xs-12">
            <div className="btn-group pull-right" role="group">
              <button
                type="button"
                className={`btn btn-secondary${
                  mode === 'traj' ? ' active' : ''
                }`}
                onClick={this.handleTrajectoryClick}
              >
                Trajectory
              </button>
              <button
                type="buttons"
                className={`btn btn-secondary${
                  mode === 'heat' ? ' active' : ''
                }`}
                onClick={this.handleHeatmapClick}
              >
                Heatmap
              </button>
            </div>
          </div>
        </div>
        <div className="row">
          <div className="col-xs-12">
            {mode === 'traj' && (
              <TrajectoryVisualizer
                fieldImg={`/images/${year}_field.png`}
                data={data}
              />
            )}
            {mode === 'heat' && (
              <HeatmapVisualizer
                fieldImg={`/images/${year}_field.png`}
                data={data}
              />
            )}
          </div>
        </div>
      </div>
    )
  }
}

ZebraMotionWorksVisualizer.propTypes = {
  data: PropTypes.object.isRequired,
  year: PropTypes.number.isRequired,
}

export default ZebraMotionWorksVisualizer
