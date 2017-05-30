import React from 'react'
import { webcastPropType } from '../../utils/webcastUtils'

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
      allowFullScreen
    />
  )
}

EmbedTwitch.propTypes = {
  webcast: webcastPropType.isRequired,
}

export default EmbedTwitch
