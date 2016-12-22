/* global videojs */
import React from 'react'
import { webcastPropType } from '../../utils/webcastUtils'

export default class EmbedHtml5 extends React.Component {
  static propTypes = {
    webcast: webcastPropType.isRequired,
  }

  componentDidMount() {
    videojs(this.props.webcast.id, {
      width: '100%',
      height: '100%',
      autoplay: true,
    })
  }

  render() {
    const src = `rtmp://${this.props.webcast.channel}&${this.props.webcast.file}`
    return (
      <video
        controls
        id={this.props.webcast.id}
        className="video-js vjs-default-skin"
      >
        <source src={src} type="rtmp/mp4" />
      </video>
    )
  }
}
