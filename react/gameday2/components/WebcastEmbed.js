import React from 'react'
import EmbedUstream from './embeds/EmbedUstream'
import EmbedYoutube from './embeds/EmbedYoutube'
import EmbedTwitch from './embeds/EmbedTwitch'
import EmbedLivestream from './embeds/EmbedLivestream'
import EmbedIframe from './embeds/EmbedIframe'
import EmbedHtml5 from './embeds/EmbedHtml5'
import EmbedDacast from './embeds/EmbedDacast'
import EmbedDirectLink from './embeds/EmbedDirectLink'
import EmbedRtmp from './embeds/EmbedRtmp'
import EmbedNotSupported from './embeds/EmbedNotSupported'
import { webcastPropType } from '../utils/webcastUtils'

export default class WebcastEmbed extends React.Component {
  static propTypes = {
    webcast: webcastPropType,
  }

  render() {
    let cellEmbed
    switch (this.props.webcast.type) {
      case 'ustream':
        cellEmbed = (<EmbedUstream webcast={this.props.webcast} />)
        break
      case 'youtube':
        cellEmbed = (<EmbedYoutube webcast={this.props.webcast} />)
        break
      case 'twitch':
        cellEmbed = (<EmbedTwitch webcast={this.props.webcast} />)
        break
      case 'livestream':
        cellEmbed = (<EmbedLivestream webcast={this.props.webcast} />)
        break
      case 'iframe':
        cellEmbed = (<EmbedIframe webcast={this.props.webcast} />)
        break
      case 'html5':
        cellEmbed = (<EmbedHtml5 webcast={this.props.webcast} />)
        break
      case 'dacast':
        cellEmbed = (<EmbedDacast webcast={this.props.webcast} />)
        break
      case 'direct_link':
        cellEmbed = (<EmbedDirectLink webcast={this.props.webcast} />)
        break
      case 'rtmp':
        cellEmbed = (<EmbedRtmp webcast={this.props.webcast} />)
        break
      default:
        cellEmbed = (<EmbedNotSupported />)
        break
    }

    return cellEmbed
  }
}
