import React, { PureComponent } from 'react'

class CurrentMatchDisplay extends PureComponent {
  render() {
    return (
      <div className='row liveEventPanel'>
        <div className='col-xs-4'>
          <div className='booleanIndicator red'>Scale</div>
          <div className='booleanIndicator red'>Switch</div>
          <div className='powerupsContainer'>
            <div className='powerupCountContainer'>
              <img src='/images/2018_force.png' className='powerupIcon' />
              <div className='powerupCount'>2</div>
            </div>
            <div className='powerupCountContainer powerupCountContainerCenter'>
              <img src='/images/2018_levitate.png' className='powerupIcon' />
              <div className='powerupCount'>1</div>
            </div>
            <div className='powerupCountContainer red'>
              <img src='/images/2018_boost.png' className='powerupIcon' />
              <div className='powerupCount'>3</div>
            </div>
          </div>
          <div className='booleanIndicator red'>Auto Quest</div>
          <div className='booleanIndicator'>Face The Boss</div>
        </div>
        <div className='col-xs-4 middleCol'>
          <div className='progress'>
            <div className='progress-bar progress-bar-success' style={{width: '50%'}}></div>
            <div className='timeRemainingContainer'>
              <span className='timeRemaining'>52</span>
            </div>
          </div>
          <div className='scoreContainer'>
            <div className='redAlliance'>
              <div>254</div>
              <div>604</div>
              <div>2135</div>
              <div className='score red'>254</div>
            </div>
            <div className='blueAlliance'>
              <div>846</div>
              <div>971</div>
              <div>8</div>
              <div className='score blue'>70</div>
            </div>
          </div>
          <div className='currentPowerup red'>
            <img src='/images/2018_force.png' className='currentPowerupIcon' />
            8
          </div>
        </div>
        <div className='col-xs-4'>
          <div className='booleanIndicator'>Scale</div>
          <div className='booleanIndicator blue'>Switch</div>
          <div className='powerupsContainer'>
            <div className='powerupCountContainer blue'>
              <img src='/images/2018_force.png' className='powerupIcon' />
              <div className='powerupCount'>2</div>
            </div>
            <div className='powerupCountContainer powerupCountContainerCenter'>
              <img src='/images/2018_levitate.png' className='powerupIcon' />
              <div className='powerupCount'>1</div>
            </div>
            <div className='powerupCountContainer blue'>
              <img src='/images/2018_boost.png' className='powerupIcon' />
              <div className='powerupCount'>3</div>
            </div>
          </div>
          <div className='booleanIndicator'>Auto Quest</div>
          <div className='booleanIndicator'>Face The Boss</div>
        </div>
      </div>
    )
  }
}

export default CurrentMatchDisplay
