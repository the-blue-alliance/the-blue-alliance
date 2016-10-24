import React from 'react'
import { WebcastPropType } from '../utils/webcastUtils'

const EmbedUstream = (props) => {
  const channel = props.webcast.channel
  const src = `http://www.ustream.tv/embed/${channel}?html5ui=1`
  return (
    <iframe
      width="100%"
      height="100%"
      src={src}
      scrolling="no"
      allowFullScreen
      frameBorder="0"
      style={{ border: '0 none transparent' }}
    />
  )
}

EmbedUstream.propTypes = {
  webcast: WebcastPropType.isRequired,
}

export default EmbedUstream
