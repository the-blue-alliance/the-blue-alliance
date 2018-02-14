import React, { PureComponent } from 'react'
import PropTypes from 'prop-types'

class PowerupCount extends PureComponent {
  render() {
    const {
      color,
      type,
      count,
      played,
      isCenter
    } = this.props
    const tooltipTitle = type.charAt(0).toUpperCase() + type.slice(1)
    return (
      <div className={`powerupCountContainer ${isCenter ? 'powerupCountContainerCenter' : ''} ${count !== 0 ? `${color}Count${count}` : ''} ${played ? color : ''}`}>
        <img src={`/images/2018_${type}.png`} className="powerupIcon" role="presentation" rel="tooltip" title={tooltipTitle} />
        <div className="powerupCount">{count}</div>
      </div>
    )
  }
}

PowerupCount.propTypes = {
  color: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  count: PropTypes.number.isRequired,
  played: PropTypes.bool.isRequired,
  isCenter: PropTypes.bool,
}

export default PowerupCount
