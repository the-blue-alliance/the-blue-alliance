import React from 'react'
import PropTypes from 'prop-types'

import { getCompLevelStr, getMatchSetStr } from '../helpers'

const LastMatchesTable = (props) => {
  if (props.matches === null) {
    return <div><span className="glyphicon glyphicon-refresh glyphicon-refresh-animate" /></div>
  } else if (props.matches.length === 0) {
    return <div>No matches have been played</div>
  }

  const matchRows = []
  props.matches.forEach((match) => {
    const year = match.key.substring(0, 4)
    matchRows.push(
      <tr key={`${match.key}_red`}>
        <td rowSpan="2"><a href={`/match/${match.key}`}>{getCompLevelStr(match)}<br />{getMatchSetStr(match)}</a></td>
        {match.alliances.red.team_keys.map((teamKey) => {
          const teamNum = teamKey.substring(3)
          return <td key={teamKey} className={`red ${match.winning_alliance === 'red' ? 'winner' : ''}`}><a href={`/team/${teamNum}/${year}`}>{teamNum}</a></td>
        })}
        <td className={`redScore ${match.winning_alliance === 'red' ? 'winner' : ''}`}>{ match.alliances.red.score }</td>
      </tr>
    )
    matchRows.push(
      <tr key={`${match.key}_blue`}>
        {match.alliances.blue.team_keys.map((teamKey) => {
          const teamNum = teamKey.substring(3)
          return <td key={teamKey} className={`blue ${match.winning_alliance === 'blue' ? 'winner' : ''}`}><a href={`/team/${teamNum}/${year}`}>{teamNum}</a></td>
        })}
        <td className={`blueScore ${match.winning_alliance === 'blue' ? 'winner' : ''}`}>{ match.alliances.blue.score }</td>
      </tr>
    )
  })

  return (
    <table className="match-table">
      <thead>
        <tr className="key">
          <th>Match</th>
          <th colSpan="3">Alliances</th>
          <th>Scores</th>
        </tr>
      </thead>
      <tbody>
        { matchRows }
      </tbody>
    </table>
  )
}

LastMatchesTable.propTypes = {
  matches: PropTypes.array,
}

export default LastMatchesTable
