import React from 'react'
import PropTypes from 'prop-types'

import { getCompLevelStr, getMatchSetStr } from '../helpers'

class UpcomingMatchesTable extends React.PureComponent {
  state = {
    currentTime: undefined,
  }

  componentDidMount() {
    this.updateCurrentTime()
    setInterval(this.updateCurrentTime, 10000)
  }

  updateCurrentTime = () => {
    this.setState({ currentTime: new Date().getTime() / 1000 })
  }

  render() {
    if (this.props.matches === null) {
      return <div><span className="glyphicon glyphicon-refresh glyphicon-refresh-animate" /></div>
    } else if (this.props.matches.length === 0) {
      return <div>There are no more scheduled matches</div>
    }

    const matchRows = []
    this.props.matches.forEach((match) => {
      let etaStr = '?'
      if (this.state.currentTime && match.pt) {
        const etaMin = (match.pt - this.state.currentTime) / 60
        if (etaMin < 2) {
          etaStr = '<2 min'
        } else if (etaMin > 120) {
          etaStr = `~${Math.round(etaMin / 60)} h`
        } else {
          etaStr = `~${Math.round(etaMin)} min`
        }
      }

      matchRows.push(
        <tr key={`${match.key}_red`}>
          <td rowSpan="2"><a href={`/match/${match.key}`}>{getCompLevelStr(match)}<br />{getMatchSetStr(match)}</a></td>
          {match.rt.map((teamKey) => {
            const teamNum = teamKey.substring(3)
            return <td key={teamKey} className="red"><a href={`/team/${teamNum}/${this.props.year}`}>{teamNum}</a></td>
          })}
          <td rowSpan="2">{ etaStr }</td>
        </tr>
      )
      matchRows.push(
        <tr key={`${match.key}_blue`}>
          {match.bt.map((teamKey) => {
            const teamNum = teamKey.substring(3)
            return <td key={teamKey} className="blue"><a href={`/team/${teamNum}/${this.props.year}`}>{teamNum}</a></td>
          })}
        </tr>
      )
    })

    return (
      <table className="match-table">
        <thead>
          <tr className="key">
            <th>Match</th>
            <th colSpan="3">Alliances</th>
            <th>ETA</th>
          </tr>
        </thead>
        <tbody>
          { matchRows }
        </tbody>
      </table>
    )
  }
}

UpcomingMatchesTable.propTypes = {
  year: PropTypes.number.isRequired,
  matches: PropTypes.arrayOf(PropTypes.object),
}

export default UpcomingMatchesTable
