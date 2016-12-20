import React from 'react'
import { webcastPropType } from '../../utils/webcastUtils'

const EmbedHtml5 = (props) => {
  const flashVars = JSON.stringify({
    plugins: {
      flashls: {
        url: '/flowplayer/flashlsFlowPlayer.swf',
        hls_maxbufferlength: 20
      }
    },
    clip: {
      live: true,
      url: `${props.webcast.channel}`,
      provider: 'flashls',
      urlResolvers: 'flashls',
      scaling: 'fit'
    }
  })
  const flashVarsConfig = `config=${flashVars}`
  return (
    <object
      width="100%"
      height="100%"
      data="/flowplayer/flowplayer-3.2.18.swf"
      type="application/x-shockwave-flash"
    >
      <param name="flashvars" value={flashVarsConfig} />
      <param name="movie" value="/flowplayer/flowplayer-3.2.18.swf" />
      <param name="allowfullscreen" value="true" />
      <param name="bgcolor" value="222222" />
    </object>
  )
}

EmbedHtml5.propTypes = {
  webcast: webcastPropType.isRequired,
}

export default EmbedHtml5
