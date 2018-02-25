import React from 'react'
import PowerupCount from '../../liveevent/components/PowerupCount'

export default class LivescoreDisplay extends React.Component {
  static propTypes = {
  }

  state = {
    matchState: {
      m: 'teleop',
      t: 22,
      rs: 157,
      rfc: 2,
      rfp: true,
      rlc: 3,
      rlp: true,
      rbc: 1,
      rbp: false,
      rswo: true,
      rsco: true,
      rcp: null,
      rpt: null,
      raq: true,
      rfb: false,
      bs: 121,
      bfc: 1,
      bfp: false,
      blc: 3,
      blp: false,
      bbc: 3,
      bbp: true,
      bswo: true,
      bsco: false,
      bcp: 'boost',
      bpt: 7,
      baq: true,
      bfb: false,
    },
  }

  render() {
    const match = {
      key: '2018week0',
      alliances: {
        'red': {
          'team_keys': ['frc254', 'frc604', 'frc8'],
        },
        'blue': {
          'team_keys': ['frc971', 'frc100', 'frc1678'],
        },
      },
    }

    const {
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
    } = this.state.matchState

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

    const year = match.key.substring(0, 4)

    return (
      <div className="livescore-display">
        <h3>
          Qual 1
        </h3>
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
    )
  }
}
