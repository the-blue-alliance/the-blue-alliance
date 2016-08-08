import React from 'react'
import classNames from 'classnames'

export default React.createClass({
  render() {
    let classes = classNames({
      'hidden': !this.props.enabled,
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
        ></iframe>
      </div>
    )
  },
})
