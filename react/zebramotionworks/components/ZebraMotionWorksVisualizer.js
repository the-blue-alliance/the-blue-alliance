import React from 'react'
import PropTypes from 'prop-types'

class ZebraMotionWorksVisualizer extends React.Component {
  generatePath = (teamData) => {
    let path = ''
    let first = true
    for (let i = 0; i < teamData.xs.length; i++) {
      if (teamData.xs[i] !== null && teamData.ys[i] !== null) {
        if (first) {
          first = false
          path = `M ${teamData.xs[i]} ${teamData.ys[i]}`
        }
        path += ` L ${teamData.xs[i]} ${teamData.ys[i]}`
      }
    }
    return path
  }

  render() {
    const { data } = this.props
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
            d={this.generatePath(data.red[0])}
            fill="none"
            stroke="#FF0000"
            strokeWidth={0.2}
          />
          <path
            d={this.generatePath(data.red[1])}
            fill="none"
            stroke="#800000"
            strokeWidth={0.2}
          />
          <path
            d={this.generatePath(data.red[2])}
            fill="none"
            stroke="#FF8080"
            strokeWidth={0.2}
          />
          <path
            d={this.generatePath(data.blue[0])}
            fill="none"
            stroke="#0000FF"
            strokeWidth={0.2}
          />
          <path
            d={this.generatePath(data.blue[1])}
            fill="none"
            stroke="#000080"
            strokeWidth={0.2}
          />
          <path
            d={this.generatePath(data.blue[2])}
            fill="none"
            stroke="#8080FF"
            strokeWidth={0.2}
          />
        </svg>
      </div>
    )
  }
}

ZebraMotionWorksVisualizer.propTypes = {
  data: PropTypes.object.isRequired,
}

export default ZebraMotionWorksVisualizer
