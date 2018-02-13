import React, { PureComponent } from 'react'

class CurrentMatchDisplay extends PureComponent {
  state = {
    mode: 'pre_match',
    timeRemaining: 15,
    redScore: 0,
    redForceCount: 0,
    redForcePlayed: false,
    redLevitateCount: 0,
    redLevitatePlayed: false,
    redBoostCount: 0,
    redBoostPlayed: false,
    redSwitchOwned: false,
    redScaleOwned: false,
    redCurrentPowerup: null,
    redPowerupTimeRemaining: null,
    redAutoQuest: false,
    redFaceTheBoss: false,
    blueScore: 0,
    blueForceCount: 0,
    blueForcePlayed: false,
    blueLevitateCount: 0,
    blueLevitatePlayed: false,
    blueBoostCount: 0,
    blueBoostPlayed: false,
    blueSwitchOwned: false,
    blueScaleOwned: false,
    blueCurrentPowerup: null,
    bluePowerupTimeRemaining: null,
    blueAutoQuest: false,
    blueFaceTheBoss: false,
  }

  componentDidMount() {
    setTimeout(this.updateState, 3000)
  }

  updateState = () => {
    if (this.state.mode === 'pre_match') {
      this.setState({
        mode: 'auto',
      })
    }

    if (this.state.mode === 'auto') {
      if (this.state.timeRemaining === 0) {
        this.setState({
          mode: 'teleop',
          timeRemaining: 136,
        })
      } else {
        if (this.state.redScaleOwned) {
          this.setState({ redScore: this.state.redScore + 2 })
        }
        if (this.state.blueScaleOwned) {
          this.setState({ blueScore: this.state.blueScore + 2 })
        }
        if (this.state.redSwitchOwned) {
          this.setState({ redScore: this.state.redScore + 2 })
        }
        if (this.state.blueSwitchOwned) {
          this.setState({ blueScore: this.state.blueScore + 2 })
        }
      }
    }

    if (this.state.mode === 'teleop') {
      if (this.state.timeRemaining === 0) {
        this.setState({
          mode: 'post_match',
        })
      } else {
        if (this.state.redScaleOwned) {
          this.setState({ redScore: this.state.redScore + (this.state.redCurrentPowerup === 'boost' ? 2 : 1) })
        }
        if (this.state.blueScaleOwned) {
          this.setState({ blueScore: this.state.blueScore + (this.state.blueCurrentPowerup === 'boost' ? 2 : 1) })
        }
        if (this.state.redSwitchOwned) {
          this.setState({ redScore: this.state.redScore + (this.state.redCurrentPowerup === 'boost' ? 2 : 1) })
        }
        if (this.state.blueSwitchOwned) {
          this.setState({ blueScore: this.state.blueScore + (this.state.blueCurrentPowerup === 'boost' ? 2 : 1) })
        }
      }
    }

    // Handle time countdown
    if (this.state.mode === 'auto' || this.state.mode === 'teleop') {
      this.setState({
        timeRemaining: this.state.timeRemaining - 1,
      })
    }

    // Handle powerup countdown
    if (this.state.redCurrentPowerup && this.state.redPowerupTimeRemaining > 0) {
      this.setState({
        redPowerupTimeRemaining: this.state.redPowerupTimeRemaining - 1,
      })
    } else {
      this.setState({ redCurrentPowerup: null, redPowerupTimeRemaining: null })
    }

    if (this.state.blueCurrentPowerup && this.state.bluePowerupTimeRemaining > 0) {
      this.setState({
        bluePowerupTimeRemaining: this.state.bluePowerupTimeRemaining - 1,
      })
    } else {
      this.setState({ blueCurrentPowerup: null, bluePowerupTimeRemaining: null })
    }

    // Call again
    if (this.state.mode !== 'post_match') {
      setTimeout(this.updateState, 100)
    }

    // Fake scale/switch events
    if (this.state.mode === 'auto' && this.state.timeRemaining === 12) {
      this.setState({ redScaleOwned: true })
    }
    if (this.state.mode === 'auto' && this.state.timeRemaining === 10) {
      this.setState({ blueSwitchOwned: true })
    }
    if (this.state.mode === 'auto' && this.state.timeRemaining === 9) {
      this.setState({ redSwitchOwned: true })
    }
    if (this.state.mode === 'auto' && this.state.timeRemaining === 7) {
      this.setState({ redAutoQuest: true })
    }
    if (this.state.mode === 'auto' && this.state.timeRemaining === 3) {
      this.setState({ blueAutoQuest: true })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 122) {
      this.setState({ redScaleOwned: false, blueScaleOwned: true })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 110) {
      this.setState({ blueSwitchOwned: false })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 90) {
      this.setState({ blueSwitchOwned: true })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 76) {
      this.setState({ redScaleOwned: true, blueScaleOwned: false })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 51) {
      this.setState({ redSwitchOwned: false })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 48) {
      this.setState({ blueSwitchOwned: false })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 34) {
      this.setState({ redSwitchOwned: true })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 25) {
      this.setState({ redScaleOwned: false, blueScaleOwned: true })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 15) {
      this.setState({ redScaleOwned: true, blueScaleOwned: false })
    }

    // Fake powerup events
    // Red Boost
    if (this.state.mode === 'teleop' && this.state.timeRemaining === 115) {
      this.setState({ redBoostCount: 1, redScore: this.state.redScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 105) {
      this.setState({ redBoostCount: 2, redScore: this.state.redScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 95) {
      this.setState({ redBoostCount: 3, redScore: this.state.redScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 72) {
      this.setState({ redBoostPlayed: true, redCurrentPowerup: 'boost', redPowerupTimeRemaining: 10 })
    }

    // Red Levitate
    if (this.state.mode === 'teleop' && this.state.timeRemaining === 77) {
      this.setState({ redLevitateCount: 1, redScore: this.state.redScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 52) {
      this.setState({ redLevitateCount: 2, redScore: this.state.redScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 31) {
      this.setState({ redLevitateCount: 3, redScore: this.state.redScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 12) {
      this.setState({ redLevitatePlayed: true })
    }

    // Blue Boost
    if (this.state.mode === 'teleop' && this.state.timeRemaining === 112) {
      this.setState({ blueBoostCount: 1, blueScore: this.state.blueScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 82) {
      this.setState({ blueBoostCount: 2, blueScore: this.state.blueScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 40) {
      this.setState({ blueBoostCount: 3, blueScore: this.state.blueScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 25) {
      this.setState({ blueBoostPlayed: true, blueCurrentPowerup: 'boost', bluePowerupTimeRemaining: 10 })
    }

    // Blue Force
    if (this.state.mode === 'teleop' && this.state.timeRemaining === 60) {
      this.setState({ blueForceCount: 1, blueScore: this.state.blueScore + 5 })
    }

    // Blue Levitate
    if (this.state.mode === 'teleop' && this.state.timeRemaining === 50) {
      this.setState({ blueLevitateCount: 1, blueScore: this.state.blueScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 47) {
      this.setState({ blueLevitateCount: 2, blueScore: this.state.blueScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 33) {
      this.setState({ blueLevitateCount: 3, blueScore: this.state.blueScore + 5 })
    }

    if (this.state.mode === 'teleop' && this.state.timeRemaining === 15) {
      this.setState({ blueLevitatePlayed: true })
    }

    // Endgame
    if (this.state.mode === 'teleop' && this.state.timeRemaining === 1) {
      this.setState({
        redScore: this.state.redScore + 60,
        blueScore: this.state.blueScore + 90,
        blueFaceTheBoss: true,
      })
    }
  }

  render() {
    const {
      mode,
      timeRemaining,
      redScore,
      redForceCount,
      redForcePlayed,
      redLevitateCount,
      redLevitatePlayed,
      redBoostCount,
      redBoostPlayed,
      redSwitchOwned,
      redScaleOwned,
      redCurrentPowerup,
      redPowerupTimeRemaining,
      redAutoQuest,
      redFaceTheBoss,
      blueScore,
      blueForceCount,
      blueForcePlayed,
      blueLevitateCount,
      blueLevitatePlayed,
      blueBoostCount,
      blueBoostPlayed,
      blueSwitchOwned,
      blueScaleOwned,
      blueCurrentPowerup,
      bluePowerupTimeRemaining,
      blueAutoQuest,
      blueFaceTheBoss,
    } = this.state

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
            <div className={`powerupCountContainer ${redForcePlayed ? 'red' : ''}`}>
              <img src="/images/2018_force.png" className="powerupIcon" role="presentation" />
              <div className="powerupCount">{redForceCount}</div>
            </div>
            <div className={`powerupCountContainer powerupCountContainerCenter ${redLevitatePlayed && 'red'}`}>
              <img src="/images/2018_levitate.png" className="powerupIcon" role="presentation" />
              <div className="powerupCount">{redLevitateCount}</div>
            </div>
            <div className={`powerupCountContainer ${redBoostPlayed ? 'red' : ''}`}>
              <img src="/images/2018_boost.png" className="powerupIcon" role="presentation" />
              <div className="powerupCount">{redBoostCount}</div>
            </div>
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
              <div>254</div>
              <div>604</div>
              <div>2135</div>
              <div className="score red">{ redScore }</div>
            </div>
            <div className="blueAlliance">
              <div>846</div>
              <div>971</div>
              <div>8</div>
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
        <div className="col-xs-4">
          <div className={`booleanIndicator ${blueScaleOwned && 'blue'}`}>Scale</div>
          <div className={`booleanIndicator ${blueSwitchOwned && 'blue'}`}>Switch</div>
          <div className="powerupsContainer">
            <div className={`powerupCountContainer ${blueForcePlayed ? 'blue' : ''}`}>
              <img src="/images/2018_force.png" className="powerupIcon" role="presentation" />
              <div className="powerupCount">{blueForceCount}</div>
            </div>
            <div className={`powerupCountContainer powerupCountContainerCenter ${blueLevitatePlayed && 'blue'}`}>
              <img src="/images/2018_levitate.png" className="powerupIcon" role="presentation" />
              <div className="powerupCount">{blueLevitateCount}</div>
            </div>
            <div className={`powerupCountContainer ${blueBoostPlayed ? 'blue' : ''}`}>
              <img src="/images/2018_boost.png" className="powerupIcon" role="presentation" />
              <div className="powerupCount">{blueBoostCount}</div>
            </div>
          </div>
          <div className={`booleanIndicator ${blueAutoQuest && 'blue'}`}>Auto Quest</div>
          <div className={`booleanIndicator ${blueFaceTheBoss && 'blue'}`}>Face The Boss</div>
        </div>
      </div>
    )
  }
}

export default CurrentMatchDisplay
