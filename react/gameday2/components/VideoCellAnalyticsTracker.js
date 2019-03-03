import React from 'react'
import ReactGA from 'react-ga'
import { webcastPropType } from '../utils/webcastUtils'

ReactGA.initialize('UA-1090782-9')

export default class VideoCellAnalyticsTracker extends React.Component {
  static propTypes = {
    webcast: webcastPropType,
  }

  constructor(props) {
    super(props)
    this.elapsedTime = 0 // In minutes
  }


  sendTracking() {
    const { key, type, channel, file } = this.props.webcast
    let action = `${key}::${type}::${channel}`
    if (file) {
      action += `::${file}`
    }

    ReactGA.event({
      category: 'Webcast View Time',
      action: action.toLowerCase(),
      label: this.elapsedTime.toString(),
      value: this.elapsedTime === 0 ? 0 : 1,
    })
    this.elapsedTime += 1
  }

  componentDidMount() {
    this.sendTracking()
    this.interval = setInterval(this.sendTracking.bind(this), 60000)
  }

  componentWillUnmount() {
    clearInterval(this.interval)
  }

  render() {
    return null
  }
}
