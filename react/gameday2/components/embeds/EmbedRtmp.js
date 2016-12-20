import React from 'react'
import { webcastPropType } from '../../utils/webcastUtils'

const EmbedRtmp = (props) => {
  const channel = props.webcast.channel
  const file = props.webcast.file
  const flashVars = `file=${file}&streamer=rtmp://${channel}&autostart=true&provider=rtmp`
  return (
    <object
      width="100%"
      height="100%"
      data="/jwplayer/player.swf"
      type="application/x-shockwave-flash"
      >
      <param name="flashvars" value={flashVars} />
      <param name="allowfullscreen" value="true" />
      <param name="background" value="transparent" />
      <param name="wmode" value="transparent" />
    </object>
  )
}

EmbedRtmp.propTypes = {
  webcast: webcastPropType.isRequired,
}

export default EmbedRtmp
