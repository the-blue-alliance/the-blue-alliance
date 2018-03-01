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
  return (compLevelsPlayOrder[match.comp_level] * 100000) + (match.match_number * 100) + match.set_number
}

class LiveEventPanel extends React.PureComponent {
  state = {
    playedMatches: null,
    unplayedMatches: null,
    matchState: null,
  }

  componentDidMount() {
    const firebaseApp = Firebase.initializeApp({
      apiKey: "AIzaSyA829V_3y57gGXIm7iodYHmkeYwXvOjL4c",
      authDomain: "thebluealliance-dev.firebaseapp.com",
      databaseURL: "https://thebluealliance-dev.firebaseio.com",
    })
    firebaseApp.database().ref(`/e/${this.props.eventKey}/m`).on('value', (snapshot) => {
      const val = snapshot.val()
      let matches
      if (val) {
        matches = Object.values(val)
      } else {
        matches = []
      }
      matches.sort((match1, match2) => playOrder(match1) - playOrder(match2))

      const playedMatches = matches.filter((match) => match.alliances.red.score !== -1 && match.alliances.blue.score !== -1)
      const unplayedMatches = matches.filter((match) => match.alliances.red.score === -1 || match.alliances.blue.score === -1)
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
      if (matchState === null) {
        upcomingMatches = unplayedMatchesCopy.slice(1, 4)
        currentMatch = unplayedMatchesCopy[0]
      } else {
        playedMatchesCopy.forEach((match, i) => {
          if (match.key.split('_')[1] === matchState.mk && matchState.m !== 'post_match') {
            currentMatch = playedMatchesCopy.splice(i, 1)[0]
          }
        })
        unplayedMatchesCopy.forEach((match, i) => {
          if (match.key.split('_')[1] === matchState.mk) {
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

    return (
      <div>
        <div className="col-lg-3 text-center livePanelColumn">
          <h4>Last Matches</h4>
          <LastMatchesTable matches={playedMatchesCopy && playedMatchesCopy.slice(-3)} />
        </div>
        <div className="col-lg-6 text-center livePanelColumn">
          <h4>Current Match: { currentMatch && `${getCompLevelStr(currentMatch)} ${getMatchSetStr(currentMatch)}` }</h4>
          <CurrentMatchDisplay match={currentMatch} matchState={matchState} forcePreMatch={forcePreMatch} />
        </div>
        <div className="col-lg-3 text-center livePanelColumn">
          <h4>Upcoming Matches</h4>
          <UpcomingMatchesTable matches={upcomingMatches} />
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
