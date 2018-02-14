import React from 'react'
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
    lastMatches: null,
    currentMatch: null,
    upcomingMatches: null,
  }

  componentDidMount() {
    // TODO: Replace with production settings
    const firebaseApp = Firebase.initializeApp({
      apiKey: "AIzaSyA829V_3y57gGXIm7iodYHmkeYwXvOjL4c",
      authDomain: "thebluealliance-dev.firebaseapp.com",
      databaseURL: "https://thebluealliance-dev.firebaseio.com",
    })
    firebaseApp.database().ref('/events/2017casj/matches').on('value', (snapshot) => {
      let matches = Object.values(snapshot.val())
      matches.sort((match1, match2) => playOrder(match1) - playOrder(match2))

      const playedMatches = matches.filter(match => match.alliances.red.score !== -1 && match.alliances.blue.score !== -1)
      const unplayedMatches = matches.filter(match => match.alliances.red.score === -1 || match.alliances.blue.score === -1)
      this.setState({
        lastMatches: playedMatches.slice(-3),
        currentMatch: unplayedMatches[0],
        upcomingMatches: unplayedMatches.slice(1, 4),
      })
    })
  }

  render () {
    return (
      <div>
        <div className="col-lg-3 text-center">
          <h4>Last Matches</h4>
          <LastMatchesTable matches={this.state.lastMatches} />
        </div>
        <div className="col-lg-6 text-center">
          <h4>Current Match: { this.state.currentMatch && `${getCompLevelStr(this.state.currentMatch)} ${getMatchSetStr(this.state.currentMatch)}` }</h4>
          <CurrentMatchDisplay match={this.state.currentMatch} />
        </div>
        <div className="col-lg-3 text-center">
          <h4>Upcoming Matches</h4>
          <UpcomingMatchesTable matches={this.state.upcomingMatches} />
        </div>
        <div className="clearfix" />
      </div>
    )
  }
}

export default LiveEventPanel
