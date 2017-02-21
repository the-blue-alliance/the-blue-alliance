import React, { PropTypes } from 'react'
import { black, white } from 'material-ui/styles/colors'

const TickerMatch = (props) => {
  const matchStyle = {
    backgroundColor: black,
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
  const matchLabelStyle = {
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
    height: '28px',
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
    lineHeight: '13px',
  }
  const blueAllianceStyle = {
    color: '#0066FF',
    fontSize: 13,
    width: 'auto',
    height: '50%',
    display: 'block',
    lineHeight: '13px',
  }

  const match = props.match

  // Set backgrounds
  if (match.winning_alliance === 'red') {  // Red win
    matchStyle.backgroundColor = '#330000'
  } else if (match.winning_alliance === 'blue') {  // Blue win
    matchStyle.backgroundColor = '#000033'
  } else if (match.alliances.red.score !== -1 && match.alliances.blue.score !== -1) {  // Tie
    matchStyle.backgroundColor = '#220022'
  } else if (props.hasFavorite) {
    matchStyle.backgroundColor = '#e6c100'
    matchLabelStyle.color = black
  }

  // Generate strings
  let compLevel = match.comp_level.toUpperCase()
  compLevel = (compLevel === 'QM') ? 'Q' : compLevel
  const matchNumber = (compLevel === 'QF' || compLevel === 'SF' || compLevel === 'F') ? `${match.set_number}-${match.match_number}` : match.match_number
  const matchLabel = `${compLevel}${matchNumber}`

  let redScore = match.alliances.red.score
  let blueScore = match.alliances.blue.score
  redScore = (redScore === -1) ? '' : ` - ${redScore}`
  blueScore = (blueScore === -1) ? '' : ` - ${blueScore}`

  return (
    <div style={matchStyle}>
      <div style={matchLabelStyle}>{matchLabel}</div>
      <div style={alliancesStyle}>
        <div style={redAllianceStyle}>
          {match.alliances.red.team_keys[0].substring(3)},{' '}
          {match.alliances.red.team_keys[1].substring(3)},{' '}
          {match.alliances.red.team_keys[2].substring(3)}
          {redScore}
        </div>
        <div style={blueAllianceStyle}>
          {match.alliances.blue.team_keys[0].substring(3)},{' '}
          {match.alliances.blue.team_keys[1].substring(3)},{' '}
          {match.alliances.blue.team_keys[2].substring(3)}
          {blueScore}
        </div>
      </div>
    </div>
  )
}

TickerMatch.propTypes = {
  match: PropTypes.object,
  hasFavorite: PropTypes.bool,
}

export default TickerMatch
