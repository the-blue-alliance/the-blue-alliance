import React from 'react'
import { WebcastPropType } from '../utils/webcastUtils'

const EmbedTwitch = (props) => {
  const channel = props.webcast.channel
  const iframeSrc = `https://player.twitch.tv/?channel=${channel}`
  return (
    <iframe
      src={iframeSrc}
      frameBorder="0"
      scrolling="no"
      height="100%"
      width="100%"
    />
  )
}

EmbedTwitch.propTypes = {
  webcast: WebcastPropType.isRequired,
}

export default EmbedTwitch
