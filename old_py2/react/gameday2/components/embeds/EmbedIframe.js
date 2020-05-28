/* eslint-disable react/no-danger */
import React from 'react'
import { webcastPropType } from '../../utils/webcastUtils'

const EmbedIframe = (props) => {
  const divStyle = {
    width: '100%',
    height: '100%',
  }

  let iframeMarkup = props.webcast.channel
  iframeMarkup = iframeMarkup.replace(/&lt;/, '<')
  iframeMarkup = iframeMarkup.replace(/&gt;/, '>')
  const markup = {
    __html: iframeMarkup,
  }

  const elem = (
    <div
      style={divStyle}
      dangerouslySetInnerHTML={markup}
    />
  )

  return elem
}

EmbedIframe.propTypes = {
  webcast: webcastPropType.isRequired,
}

export default EmbedIframe
