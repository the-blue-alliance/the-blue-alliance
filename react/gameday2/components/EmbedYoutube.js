import React from 'react'
import { WebcastPropType } from '../utils/webcastUtils'

const EmbedYoutube = (props) => {
  const src = `//www.youtube.com/embed/${props.webcast.channel}`
  return (
    <iframe
      width="100%"
      height="100%"
      src={src}
      frameBorder="0"
      allowFullScreen
    />
  )
}

EmbedYoutube.propTypes = {
  webcast: WebcastPropType.isRequired,
}

export default EmbedYoutube
