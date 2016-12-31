import React, { PropTypes } from 'react'
import { List, ListItem } from 'material-ui/List'
import { fullWhite } from 'material-ui/styles/colors'
import { chatPropType } from '../utils/PropTypes'

export default class ChatSelector extends React.Component {
  static propTypes = {
    chats: PropTypes.objectOf(chatPropType).isRequired,
    currentChat: PropTypes.string.isRequired,
    setTwitchChat: PropTypes.func.isRequired,
    open: PropTypes.bool.isRequired,
    onRequestClose: PropTypes.func.isRequired,
  }

  setTwitchChat(e, channel) {
    //e.stopPropagation()
    this.props.setTwitchChat(channel)
    this.props.onRequestClose()
  }

  render() {
    // TODO: make this a selector
    const chats = []
    Object.keys(this.props.chats)
    .filter((key) => ({}.hasOwnProperty.call(this.props.chats, key)))
    .forEach((key) => chats.push(this.props.chats[key]))

    const chatItems = []
    chats.forEach((chat) => {
      chatItems.push(
        <ListItem
          primaryText={chat.name}
          onTouchTap={(e) => this.setTwitchChat(e, chat.channel)}
          key={chat.channel}
        />
      )
    })

    const containerStyle = {
      width: '100%',
      height: '100%',
      background: 'rgba(0,0,0,0.7)',
      position: 'absolute',
    }

    const listStyle = {
      width: '100%',
      position: 'absolute',
      bottom: 0,
      background: fullWhite,
    }

    if (this.props.open) {
      return (
        <div
          style={containerStyle}
          onTouchTap={() => this.props.onRequestClose()}>
          <List
            style={listStyle}
            onTouchTap={(e) => e.stopPropagation()}>
            {chatItems}
          </List>
        </div>
      )
    }

    return (<div></div>)
  }
}
