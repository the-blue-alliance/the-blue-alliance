import React from 'react'
import PropTypes from 'prop-types'

const HatchCargoCount = (props) => {
  const {
    name,
    hatches,
    cargo,
    style,
  } = props

  const svgStyle = {
    display: 'inline-block',
    verticalAlign: 'middle',
  }

  const panelIndicator = () => (
    <svg width="16px" height="16px" style={svgStyle} rel="tooltip" title="Hatch Panel">
      <circle cx="8" cy="8" r="6" fill="none" stroke="#f4d941" strokeWidth="4" />
    </svg>
  )

  const cargoIndicator = () => (
    <svg width="16px" height="16px" style={svgStyle} rel="tooltip" title="Cargo">
      <circle cx="8" cy="8" r="8" fill="#ffa500" />
    </svg>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', ...style }}>
      <span style={{ fontSize: 9, margin: 'auto' }}>{name}</span>
      <span>{cargoIndicator()} {cargo || 0}</span>
      <span>{panelIndicator()} {hatches || 0}</span>
    </div>
  )
}

HatchCargoCount.propTypes = {
  name: PropTypes.string.isRequired,
  hatches: PropTypes.number.isRequired,
  cargo: PropTypes.number.isRequired,
  style: PropTypes.object,
}

export default HatchCargoCount
