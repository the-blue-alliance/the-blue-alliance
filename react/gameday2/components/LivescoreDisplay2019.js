import React from 'react'
import PropTypes from 'prop-types'
import AutoScale from './AutoScale/AutoScale'
import CountWrapper from './CountWrapper'
import HatchCargoCount from '../../liveevent/components/HatchCargoCount'

class LivescoreDisplay2019 extends React.PureComponent {
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
    const { matches, matchState } = this.props

    if (!matchState) {
      return (
        <div className="livescore-wrapper">
          <div className="livescore-container">
            <div className="livescore-display">Live match info not available</div>
          </div>
        </div>
      )
    }

    let {
      m: mode,
      t: timeRemaining,
      rs: redScore,
      rcsh: redCargoShipHatchCount,
      rcsc: redCargoShipCargoCount,
      rr1h: redRocket1HatchCount,
      rr1c: redRocket1CargoCount,
      rr2h: redRocket2HatchCount,
      rr2c: redRocket2CargoCount,
      rrrp: redRocketRankingPoint,
      rhrp: redHabRankingPoint,
      bs: blueScore,
      bcsh: blueCargoShipHatchCount,
      bcsc: blueCargoShipCargoCount,
      br1h: blueRocket1HatchCount,
      br1c: blueRocket1CargoCount,
      br2h: blueRocket2HatchCount,
      br2c: blueRocket2CargoCount,
      brrp: blueRocketRankingPoint,
      bhrp: blueHabRankingPoint,
    } = matchState

    let match
    let nextMatch
    matches.forEach((m) => {
      // Find current match
      if (m.shortKey === matchState.mk) {
        match = m
      }
      // Find next unplayed match after current match
      if (match && !nextMatch) {
        if (m.r === -1 && m.b === -1) {
          nextMatch = m
        }
      }
    })

    let showETA = false
    if (mode === 'post_match' && match && match.r !== -1 && match.b !== -1) {
      // If match has been played, display next match and ETA
      match = nextMatch
      showETA = true
    } else if (mode === 'pre_match') {
      // If match mode is pre_match, display match and ETA
      showETA = true
    }

    if (!match) {
      return (
        <div className="livescore-wrapper">
          <div className="livescore-container">
            <div className="livescore-display">Live match info not available</div>
          </div>
        </div>
      )
    }

    let etaStr = ''
    if (showETA) {  // Reset to pre match defaults
      mode = 'pre_match'
      timeRemaining = 0
      redCargoShipHatchCount = 0
      redCargoShipCargoCount = 0
      redRocket1HatchCount = 0
      redRocket1CargoCount = 0
      redRocket2HatchCount = 0
      redRocket2CargoCount = 0
      redRocketRankingPoint = false
      redHabRankingPoint = false
      blueScore = 0
      blueCargoShipHatchCount = 0
      blueCargoShipCargoCount = 0
      blueRocket1HatchCount = 0
      blueRocket1CargoCount = 0
      blueRocket2HatchCount = 0
      blueRocket2CargoCount = 0
      blueRocketRankingPoint = false
      blueHabRankingPoint = false

      if (this.state.currentTime && match.pt) {
        const etaMin = (match.pt - this.state.currentTime) / 60
        if (etaMin < 2) {
          etaStr = ' in <2 min'
        } else if (etaMin > 120) {
          etaStr = ` in ~${Math.round(etaMin / 60)} h`
        } else {
          etaStr = ` in ~${Math.round(etaMin)} min`
        }
      } else {
        etaStr = ' is next'
      }
    }

    let compLevel = match.c.toUpperCase()
    compLevel = (compLevel === 'QM') ? 'Q' : compLevel
    const matchNumber = (compLevel === 'QF' || compLevel === 'SF' || compLevel === 'F') ? `${match.s}-${match.m}` : match.m
    const matchLabel = `${compLevel}${matchNumber}${etaStr}`

    let progressColor
    if (mode === 'post_match' || (timeRemaining === 0 && mode === 'teleop')) {
      progressColor = 'progress-bar-red'
    } else if (timeRemaining <= 30 && mode === 'teleop') {
      progressColor = 'progress-bar-yellow'
    } else {
      progressColor = 'progress-bar-green'
    }

    let progressWidth
    if (mode === 'post_match') {
      progressWidth = '100%'
    } else if (mode === 'teleop') {
      progressWidth = `${((150 - timeRemaining) * 100) / 150}%`
    } else if (mode === 'auto') {
      progressWidth = `${((15 - timeRemaining) * 100) / 150}%`
    } else {
      progressWidth = '0%'
    }

    return (
      <AutoScale
        wrapperClass="livescore-wrapper"
        containerClass="livescore-container"
        maxWidth={800}
      >
        <div className="livescore-display">
          <h3>
            { matchLabel }
          </h3>
          <div className="col-container">
            <div className="side-col">
              <div className="powerupsContainer">
                <HatchCargoCount name="Rocket 2" hatches={redRocket2HatchCount} cargo={redRocket2CargoCount} style={{ width: '30%' }} />
                <HatchCargoCount name="Cargo Ship" hatches={redCargoShipHatchCount} cargo={redCargoShipCargoCount} style={{ width: '40%' }} />
                <HatchCargoCount name="Rocket 1" hatches={redRocket1HatchCount} cargo={redRocket1CargoCount} style={{ width: '30%' }} />
              </div>
              <div className={`booleanIndicator ${redRocketRankingPoint && 'red'}`}>Complete Rocket</div>
              <div className={`booleanIndicator ${redHabRankingPoint && 'red'}`}>HAB Climb</div>
            </div>
            <div className="mid-col">
              <div className="progress">
                <div className={`progress-bar ${progressColor}`} style={{ width: progressWidth }} />
                <div className="timeRemainingContainer">
                  <span className="timeRemaining">{ timeRemaining }</span>
                </div>
              </div>
              <div className="scoreContainer">
                <div className="redAlliance">
                  {match.rt.map((teamKey) => {
                    const teamNum = teamKey.substring(3)
                    return <div key={teamKey} >{teamNum}</div>
                  })}
                  <div className="score red"><CountWrapper number={redScore} /></div>
                </div>
                <div className="blueAlliance">
                  {match.bt.map((teamKey) => {
                    const teamNum = teamKey.substring(3)
                    return <div key={teamKey} >{teamNum}</div>
                  })}
                  <div className="score blue"><CountWrapper number={blueScore} /></div>
                </div>
              </div>
            </div>
            <div className="side-col">
              <div className="powerupsContainer">
                <HatchCargoCount name="Rocket 1" hatches={blueRocket1HatchCount} cargo={blueRocket1CargoCount} style={{ width: '30%' }} />
                <HatchCargoCount name="Cargo Ship" hatches={blueCargoShipHatchCount} cargo={blueCargoShipCargoCount} style={{ width: '40%' }} />
                <HatchCargoCount name="Rocket 2" hatches={blueRocket2HatchCount} cargo={blueRocket2CargoCount} style={{ width: '30%' }} />
              </div>
              <div className={`booleanIndicator ${blueRocketRankingPoint && 'blue'}`}>Complete Rocket</div>
              <div className={`booleanIndicator ${blueHabRankingPoint && 'blue'}`}>HAB Climb</div>
            </div>
          </div>
        </div>
      </AutoScale>
    )
  }
}

LivescoreDisplay2019.propTypes = {
  matches: PropTypes.list,
  matchState: PropTypes.object,
}

export default LivescoreDisplay2019
