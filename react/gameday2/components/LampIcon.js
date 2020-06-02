import React, { PropTypes } from 'react'

const LampIcon = (props) => {
  const {
    width,
    height,
  } = props

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={width}
      height={height}
      viewBox="0 0 240 240"
    >
      <g
        transform="matrix(1.25,0,0,-1.25,0,240)"
      >
        <path
          style={{ fill: 'none', stroke: '#ffffff', strokeWidth: 6, strokeLinecap: 'butt', strokeOpacity: 1 }}
          d="M 71,132 71,68"
        />
        <path
          style={{ fill: 'none', stroke: '#ffffff', strokeWidth: 6, strokeLinecap: 'butt', strokeOpacity: 1 }}
          d="m 121,132 0,-64"
        />
        <path
          style={{ fill: 'none', stroke: '#ffffff', strokeWidth: 6, strokeLinecap: 'butt', strokeOpacity: 1 }}
          d="M 71,68 C 71,54.182 82.182,43 96,43"
        />
        <path
          style={{ fill: 'none', stroke: '#ffffff', strokeWidth: 6, strokeLinecap: 'butt', strokeOpacity: 1 }}
          d="M 121,68 C 121,54.182 109.818,43 96,43"
        />
        <path
          style={{ fill: 'none', stroke: '#ffffff', strokeWidth: 6, strokeLinecap: 'butt', strokeOpacity: 1 }}
          d="M 96,132 96,43"
        />
        <path
          style={{ fill: 'none', stroke: '#ffffff', strokeWidth: 6, strokeLinecap: 'butt', strokeOpacity: 1 }}
          d="m 71,71 50,0"
        />
        <path
          style={{ fill: 'none', stroke: '#ffffff', strokeWidth: 6, strokeLinecap: 'butt', strokeOpacity: 1 }}
          d="m 71,99 50,0"
        />
        <path
          style={{ fill: '#ffffff', stroke: 'none', fillRule: 'nonzero' }}
          d="m 132,128 c 0,-2.2 -1.8,-4 -4,-4 l -64,0 c -2.2,0 -4,1.8 -4,4 l 0,20 c 0,2.2 1.8,4 4,4 l 64,0 c 2.2,0 4,-1.8 4,-4 l 0,-20 z"
        />
      </g>
    </svg>
  )
}

LampIcon.propTypes = {
  width: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number,
  ]),
  height: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number,
  ]),
}

LampIcon.defaultProps = {
  width: 48,
  height: 48,
}

export default LampIcon
