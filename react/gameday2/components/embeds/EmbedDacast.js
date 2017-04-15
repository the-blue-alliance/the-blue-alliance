import React from 'react'
import { webcastPropType } from '../../utils/webcastUtils'

const EmbedDacast = (props) => {
  const channel = props.webcast.channel
  const file = props.webcast.file
  const iframeSrc = `https://iframe.dacast.com/b/${channel}/c/${file}`
  return (
    <iframe
      src={iframeSrc}
      width="100%"
      height="100%"
      frameBorder="0"
      scrolling="no"
      player="vjs5"
      autoPlay="true"
      allowFullScreen
      webkitallowfullscreen
      mozallowfullscreen
      oallowfullscreen
      msallowfullscreen
    />
  )
}

EmbedDacast.propTypes = {
  webcast: webcastPropType.isRequired,
}

export default EmbedDacast
