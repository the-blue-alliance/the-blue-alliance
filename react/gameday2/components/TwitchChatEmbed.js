import React, { PropTypes } from 'react'

export default class TwitchChatEmbed extends React.Component {
  static propTypes = {
    channel: PropTypes.string.isRequired,
    visible: PropTypes.bool.isRequired,
  }

  render() {
    const id = `twich-chat-${this.props.channel}`
    const src = `https://twitch.tv/chat/embed?channel=${this.props.channel}&amp;popout_chat=true`
    const style = {
      visibility: this.props.visible ? null : 'none'
    }

    <div style={style}>
      <iframe
        frameBorder="0"
        scrolling="no"
        id={id}
        src={src}
        height="100%"
        width="100%"
      />
    </div>
  }
}
