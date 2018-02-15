import React from 'react'
import PropTypes from 'prop-types'

const PowerupCount = (props) => {
  const {
    color,
    type,
    count,
    played,
    isCenter,
  } = props
  const tooltipTitle = type.charAt(0).toUpperCase() + type.slice(1)
  return (
    <div className={`powerupCountContainer ${isCenter ? 'powerupCountContainerCenter' : ''} ${count !== 0 ? `${color}Count${count}` : ''} ${played ? color : ''}`}>
      <img src={`/images/2018_${type}.png`} className="powerupIcon" role="presentation" rel="tooltip" title={tooltipTitle} />
      <div className={`powerCube ${count > 2 ? 'powerCubeActive' : ''}`} />
      <div className={`powerCube ${count > 1 ? 'powerCubeActive' : ''}`} />
      <div className={`powerCube ${count > 0 ? 'powerCubeActive' : ''}`} />
    </div>
  )
}

PowerupCount.propTypes = {
  color: PropTypes.string.isRequired,
  type: PropTypes.string.isRequired,
  count: PropTypes.number.isRequired,
  played: PropTypes.bool.isRequired,
  isCenter: PropTypes.bool,
}

export default PowerupCount
