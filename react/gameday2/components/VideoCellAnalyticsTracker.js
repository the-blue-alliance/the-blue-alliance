import React from 'react'
import ReactGA from 'react-ga'
import { webcastPropType } from '../utils/webcastUtils'

export default class VideoCellAnalyticsTracker extends React.Component {
  static propTypes = {
    webcast: webcastPropType,
  }

  constructor(props) {
    super(props)
    this.elapsedTime = 0 // In minutes
  }

  componentDidMount() {
    this.sendTracking()
    this.interval = setInterval(this.sendTracking.bind(this), 60000)
  }

  componentWillUnmount() {
    clearInterval(this.interval)
  }

  sendTracking() {
    const { id, type, channel, file } = this.props.webcast
    let action = `${id}::${type}::${channel}`
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

  render() {
    return null
  }
}
