import React from 'react'
import PropTypes from 'prop-types'

import PowerupCount from './PowerupCount'
import CountWrapper from '../../gameday2/components/CountWrapper'

const CurrentMatchDisplay = (props) => {
  const { match, matchState, forcePreMatch } = props

  if (match === null) {
    return <div><span className="glyphicon glyphicon-refresh glyphicon-refresh-animate" /></div>
  }
  if (!matchState) {
    return <div>Live match info not available</div>
  }

  let {
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

  if (forcePreMatch) {
    mode = 'pre_match'
    timeRemaining = 0
    redScore = 0
    redForceCount = 0
    redForcePlayed = false
    redLevitateCount = 0
    redLevitatePlayed = false
    redBoostCount = 0
    redBoostPlayed = false
    redSwitchOwned = 0
    redScaleOwned = 0
    redCurrentPowerup = null
    redPowerupTimeRemaining = null
    redAutoQuest = false
    redFaceTheBoss = false
    blueScore = 0
    blueForceCount = 0
    blueForcePlayed = false
    blueLevitateCount = 0
    blueLevitatePlayed = false
    blueBoostCount = 0
    blueBoostPlayed = false
    blueSwitchOwned = false
    blueScaleOwned = false
    blueCurrentPowerup = null
    bluePowerupTimeRemaining = null
    blueAutoQuest = false
    blueFaceTheBoss = false
  }

  let progressColor
  if (mode === 'post_match' || (timeRemaining === 0 && mode === 'teleop')) {
    progressColor = 'progress-bar-danger'
  } else if (timeRemaining <= 30 && mode === 'teleop') {
    progressColor = 'progress-bar-warning'
  } else {
    progressColor = 'progress-bar-success'
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
    <div className="row liveEventPanel">
      <div className="col-xs-4">
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
      <div className="col-xs-4 middleCol">
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
              return <div key={teamKey} ><a href={`/team/${teamNum}/${props.year}`}>{teamNum}</a></div>
            })}
            <div className="score red"><CountWrapper number={redScore} /></div>
          </div>
          <div className="blueAlliance">
            {match.bt.map((teamKey) => {
              const teamNum = teamKey.substring(3)
              return <div key={teamKey} ><a href={`/team/${teamNum}/${props.year}`}>{teamNum}</a></div>
            })}
            <div className="score blue"><CountWrapper number={blueScore} /></div>
          </div>
        </div>
        {currentPowerup &&
          <div className={`currentPowerup ${powerupColor}`}>
            <img src={`/images/2018_${currentPowerup}.png`} className="currentPowerupIcon" role="presentation" />
            { powerupTimeRemaining }
          </div>
        }
      </div>
      <div className="col-xs-4">
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
  )
}

CurrentMatchDisplay.propTypes = {
  year: PropTypes.number.isRequired,
  match: PropTypes.object,
  matchState: PropTypes.object,
  forcePreMatch: PropTypes.boolean,
}

export default CurrentMatchDisplay
