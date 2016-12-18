import React, { PropTypes } from 'react'
import classNames from 'classnames'

const ChatSidebar = (props) => {
  const classes = classNames({
    'chat-sidebar': true,
  })

  const style = {
    display: props.enabled ? null : 'none'
  }

  let content
  if (props.hasBeenVisible) {
    content = (
      <div className={classes} style={style}>
        <iframe
          frameBorder="0"
          scrolling="no"
          id="chat_embed"
          src="https://twitch.tv/chat/embed?channel=tbagameday&amp;popout_chat=true"
          height="100%"
          width="100%"
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
