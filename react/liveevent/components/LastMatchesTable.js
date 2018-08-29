import React from 'react'
import PropTypes from 'prop-types'

import { getCompLevelStr, getMatchSetStr } from '../helpers'

const LastMatchesTable = (props) => {
  const { year, matches } = props

  if (matches === null) {
    return <div><span className="glyphicon glyphicon-refresh glyphicon-refresh-animate" /></div>
  } else if (matches.length === 0) {
    return <div>No matches have been played</div>
  }

  const matchRows = []
  matches.forEach((match) => {
    matchRows.push(
      <tr key={`${match.key}_red`}>
        <td rowSpan="2"><a href={`/match/${match.key}`}>{getCompLevelStr(match)}<br />{getMatchSetStr(match)}</a></td>
        {match.rt.map((teamKey) => {
          const teamNum = teamKey.substring(3)
          return <td key={teamKey} className={`red ${match.w === 'red' ? 'winner' : ''}`}><a href={`/team/${teamNum}/${year}`}>{teamNum}</a></td>
        })}
        <td className={`redScore ${match.w === 'red' ? 'winner' : ''}`}>{ match.r }</td>
      </tr>
    )
    matchRows.push(
      <tr key={`${match.key}_blue`}>
        {match.bt.map((teamKey) => {
          const teamNum = teamKey.substring(3)
          return <td key={teamKey} className={`blue ${match.w === 'blue' ? 'winner' : ''}`}><a href={`/team/${teamNum}/${year}`}>{teamNum}</a></td>
        })}
        <td className={`blueScore ${match.w === 'blue' ? 'winner' : ''}`}>{ match.b }</td>
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
  year: PropTypes.number.isRequired,
  matches: PropTypes.arrayOf(PropTypes.object),
}

export default LastMatchesTable
