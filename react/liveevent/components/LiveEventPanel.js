import React from 'react'
import PropTypes from 'prop-types'
import Firebase from 'firebase'

import { getCompLevelStr, getMatchSetStr } from '../helpers'

import CurrentMatchDisplay from './CurrentMatchDisplay'
import LastMatchesTable from './LastMatchesTable'
import UpcomingMatchesTable from './UpcomingMatchesTable'

const compLevelsPlayOrder = {
  qm: 1,
  ef: 2,
  qf: 3,
  sf: 4,
  f: 5,
}

function playOrder(match) {
  return (compLevelsPlayOrder[match.c] * 100000) + (match.m * 100) + match.s
}

class LiveEventPanel extends React.PureComponent {
  state = {
    playedMatches: null,
    unplayedMatches: null,
    matchState: null,
  }

  componentDidMount() {
    const firebaseApp = Firebase.initializeApp({
      apiKey: 'AIzaSyDBlFwtAgb2i7hMCQ5vBv44UEKVsA543hs',
      authDomain: 'tbatv-prod-hrd.firebaseapp.com',
      databaseURL: 'https://tbatv-prod-hrd.firebaseio.com',
    })
    firebaseApp.database().ref(`/e/${this.props.eventKey}/m`).on('value', (snapshot) => {
      const val = snapshot.val()
      const matches = []
      if (val) {
        Object.keys(val).forEach((shortKey) => {
          const match = val[shortKey]
          match.key = `${this.props.eventKey}_${shortKey}`
          match.shortKey = shortKey
          matches.push(match)
        })
      }
      matches.sort((match1, match2) => playOrder(match1) - playOrder(match2))

      const playedMatches = matches.filter((match) => match.r !== -1 && match.b !== -1)
      const unplayedMatches = matches.filter((match) => match.r === -1 || match.b === -1)
      this.setState({
        playedMatches,
        unplayedMatches,
      })
    })
    firebaseApp.database().ref(`/le/${this.props.eventKey}`).on('value', (snapshot) => {
      this.setState({
        matchState: snapshot.val(),
      })
    })
  }

  render() {
    const { playedMatches, unplayedMatches, matchState } = this.state

    const playedMatchesCopy = playedMatches && playedMatches.slice()
    const unplayedMatchesCopy = unplayedMatches && unplayedMatches.slice()

    let upcomingMatches = null
    let currentMatch = null
    let forcePreMatch = false
    if (unplayedMatchesCopy !== null) {
      if (matchState === null || matchState.mk.startsWith('pm')) {
        upcomingMatches = unplayedMatchesCopy.slice(0, 3)
      } else {
        playedMatchesCopy.forEach((match, i) => {
          if (match.shortKey === matchState.mk && matchState.m !== 'post_match') {
            currentMatch = playedMatchesCopy.splice(i, 1)[0]
          }
        })
        unplayedMatchesCopy.forEach((match, i) => {
          if (match.shortKey === matchState.mk) {
            currentMatch = unplayedMatchesCopy.splice(i, 1)[0]
          }
        })
        if (!currentMatch) {  // Must have been in playedMatches, but mode is post_match
          currentMatch = unplayedMatchesCopy.splice(0, 1)[0]
          forcePreMatch = true
        }
        upcomingMatches = unplayedMatchesCopy.slice(0, 3)
      }
    }

    const year = parseInt(this.props.eventKey.substring(0, 4), 10)
    return (
      <div>
        <div className={`${currentMatch ? 'col-lg-3' : 'col-lg-6'} text-center livePanelColumn`}>
          <h4>Last Matches</h4>
          <LastMatchesTable year={year} matches={playedMatchesCopy && playedMatchesCopy.slice(-3)} />
        </div>
        {currentMatch &&
        <div className="col-lg-6 text-center livePanelColumn">
          <h4>Current Match: { currentMatch && `${getCompLevelStr(currentMatch)} ${getMatchSetStr(currentMatch)}` }</h4>
          <CurrentMatchDisplay year={year} match={currentMatch} matchState={matchState} forcePreMatch={forcePreMatch} />
        </div>
        }
        <div className={`${currentMatch ? 'col-lg-3' : 'col-lg-6'} text-center livePanelColumn`}>
          <h4>Upcoming Matches</h4>
          <UpcomingMatchesTable year={year} matches={upcomingMatches} />
        </div>
        <div className="clearfix" />
      </div>
    )
  }
}

LiveEventPanel.propTypes = {
  eventKey: PropTypes.string.isRequired,
}

export default LiveEventPanel
