import React, { PropTypes } from 'react'
import classNames from 'classnames'

const ChatSidebar = (props) => {
  const classes = classNames({
    hidden: !props.enabled,
    'chat-sidebar': true,
  })
  return (
    <div className={classes}>
      <iframe
        frameBorder="0"
        scrolling="no"
        id="chat_embed"
        src="http://twitch.tv/chat/embed?channel=tbagameday&amp;popout_chat=true"
        height="100%"
        width="100%"
      />
    </div>
  )
}

ChatSidebar.propTypes = {
  enabled: PropTypes.bool,
}

export default ChatSidebar
