import React from 'react'
import { black, grey900, white } from 'material-ui/styles/colors'

const TickerMatch = (props) => {
  const matchStyle = {
    height: '100%',
    width: 'auto',
    borderRadius: 2,
    marginRight: 5,
    marginLeft: 5,
    paddingRight: 10,
    paddingLeft: 10,
    display: 'inline-block',
    WebkitBoxShadow: 'rgba(0, 0, 0, 0.5) 0px 1px 6px, rgba(0, 0, 0, 0.5) 0px 1px 4px',
    MozBoxShadow: 'rgba(0, 0, 0, 0.5) 0px 1px 6px, rgba(0, 0, 0, 0.5) 0px 1px 4px',
    BoxShadow: 'rgba(0, 0, 0, 0.5) 0px 1px 6px, rgba(0, 0, 0, 0.5) 0px 1px 4px',
  }
  const matchNumberStyle = {
    color: white,
    fontSize: 16,
    width: 'auto',
    display: 'inline-block',
    lineHeight: '36px',
    marginRight: 10,
    float: 'left',
  }
  const alliancesStyle = {
    display: 'inline-block',
    height: '100%',
    width: 'auto',
    float: 'left',
    marginTop: 5,
    fontWeight: 'bold',
  }
  const redAllianceStyle = {
    color: '#FF0000',
    fontSize: 13,
    width: 'auto',
    height: '50%',
    display: 'block',
  }
  const blueAllianceStyle = {
    color: '#0066FF',
    fontSize: 13,
    width: 'auto',
    height: '50%',
    display: 'block',
  }
  if (props.matchType === 'finishedRed') {
    matchStyle.backgroundColor = '#330000'
  } else if (props.matchType === 'finishedBlue') {
    matchStyle.backgroundColor = '#000033'
  } else if (props.matchType === 'finishedTie') {
    matchStyle.backgroundColor = '#220022'
  } else if (props.matchType === 'followed') {
    matchStyle.backgroundColor = '#e6c100'
    matchNumberStyle.color = black
  } else {
    matchStyle.backgroundColor = black
  }

  return (
    <div style={matchStyle}>
      <div style={matchNumberStyle}>QF1-1</div>
      <div style={alliancesStyle}>
        <div style={redAllianceStyle}>
          6324, 1153, 78 - 145
        </div>
        <div style={blueAllianceStyle}>
          501, 58, 88 - 160
        </div>
      </div>
    </div>
  )
}

export default TickerMatch
