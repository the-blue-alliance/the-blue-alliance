import React, { PropTypes } from 'react'
import classNames from 'classnames'
import TwitchChatEmbed from './TwitchChatEmbed'

const ChatSidebar = (props) => {
  const classes = classNames({
    'chat-sidebar': true,
  })

  const style = {
    display: props.enabled ? null : 'none',
  }

  let content
  if (props.hasBeenVisible) {
    content = (
      <div className={classes} style={style}>
        <TwitchChatEmbed
          channel="tbagameday"
          visible
        />
      </div>
    )
  } else {
    content = (<div />)
  }

  return content
}

ChatSidebar.propTypes = {
  enabled: PropTypes.bool,
  hasBeenVisible: PropTypes.bool,
}

export default ChatSidebar
