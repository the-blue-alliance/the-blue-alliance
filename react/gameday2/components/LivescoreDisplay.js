import React from 'react'
import AutoScale from './AutoScale/AutoScale'
import PowerupCount from '../../liveevent/components/PowerupCount'

export default class LivescoreDisplay extends React.Component {
  static propTypes = {
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

    const {
      mk: matchKey,
      m: mode,
      t: timeRemaining,
      rs: redScore,
      rfc: redForceCount,
      rfp: redForcePlayed,
      rlc: redLevitateCount,
      rlp: redLevitatePlayed,
      rbc: redBoostCount,
      rbp: redBoostPlayed,
      rswo: redSwitchOwned,
      rsco: redScaleOwned,
      rcp: redCurrentPowerup,
      rpt: redPowerupTimeRemaining,
      raq: redAutoQuest,
      rfb: redFaceTheBoss,
      bs: blueScore,
      bfc: blueForceCount,
      bfp: blueForcePlayed,
      blc: blueLevitateCount,
      blp: blueLevitatePlayed,
      bbc: blueBoostCount,
      bbp: blueBoostPlayed,
      bswo: blueSwitchOwned,
      bsco: blueScaleOwned,
      bcp: blueCurrentPowerup,
      bpt: bluePowerupTimeRemaining,
      baq: blueAutoQuest,
      bfb: blueFaceTheBoss,
    } = matchState

    let match = null
    for (let m of matches) {
      if (m.key.split('_')[1] == matchKey) {
        match = m
        break
      }
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

    let compLevel = match.comp_level.toUpperCase()
    compLevel = (compLevel === 'QM') ? 'Q' : compLevel
    const matchNumber = (compLevel === 'QF' || compLevel === 'SF' || compLevel === 'F') ? `${match.set_number}-${match.match_number}` : match.match_number
    let matchLabel = `${compLevel}${matchNumber}`

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

    let currentPowerup = null
    let powerupTimeRemaining = null
    let powerupColor = null
    if (redCurrentPowerup) {
      currentPowerup = redCurrentPowerup
      powerupTimeRemaining = redPowerupTimeRemaining
      powerupColor = 'red'
    } else if (blueCurrentPowerup) {
      currentPowerup = blueCurrentPowerup
      powerupTimeRemaining = bluePowerupTimeRemaining
      powerupColor = 'blue'
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
              <div className={`booleanIndicator ${redScaleOwned && 'red'}`}>Scale</div>
              <div className={`booleanIndicator ${redSwitchOwned && 'red'}`}>Switch</div>
              <div className="powerupsContainer">
                <PowerupCount color="red" type="force" count={redForceCount} played={redForcePlayed} />
                <PowerupCount color="red" type="levitate" count={redLevitateCount} played={redLevitatePlayed} isCenter />
                <PowerupCount color="red" type="boost" count={redBoostCount} played={redBoostPlayed} />
              </div>
              <div className={`booleanIndicator ${redAutoQuest && 'red'}`}>Auto Quest</div>
              <div className={`booleanIndicator ${redFaceTheBoss && 'red'}`}>Face The Boss</div>
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
                  {match.alliances.red.team_keys.map((teamKey) => {
                    const teamNum = teamKey.substring(3)
                    return <div key={teamKey} >{teamNum}</div>
                  })}
                  <div className="score red">{ redScore }</div>
                </div>
                <div className="blueAlliance">
                  {match.alliances.blue.team_keys.map((teamKey) => {
                    const teamNum = teamKey.substring(3)
                    return <div key={teamKey} >{teamNum}</div>
                  })}
                  <div className="score blue">{ blueScore }</div>
                </div>
              </div>
              {currentPowerup &&
                <div className={`currentPowerup ${powerupColor}`}>
                  <img src={`/images/2018_${currentPowerup}.png`} className="currentPowerupIcon" role="presentation" />
                  <br />
                  { powerupTimeRemaining }
                </div>
              }
            </div>
            <div className="side-col">
              <div className={`booleanIndicator ${blueScaleOwned && 'blue'}`}>Scale</div>
              <div className={`booleanIndicator ${blueSwitchOwned && 'blue'}`}>Switch</div>
              <div className="powerupsContainer">
                <PowerupCount color="blue" type="force" count={blueForceCount} played={blueForcePlayed} />
                <PowerupCount color="blue" type="levitate" count={blueLevitateCount} played={blueLevitatePlayed} isCenter />
                <PowerupCount color="blue" type="boost" count={blueBoostCount} played={blueBoostPlayed} />
              </div>
              <div className={`booleanIndicator ${blueAutoQuest && 'blue'}`}>Auto Quest</div>
              <div className={`booleanIndicator ${blueFaceTheBoss && 'blue'}`}>Face The Boss</div>
            </div>
          </div>
        </div>
      </AutoScale>
    )
  }
}
