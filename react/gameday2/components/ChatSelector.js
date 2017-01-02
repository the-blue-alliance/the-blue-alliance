import React, { PropTypes } from 'react'
import ReactTransitionGroup from 'react-addons-transition-group'
import { List, ListItem } from 'material-ui/List'
import Paper from 'material-ui/Paper'
import CheckmarkIcon from 'material-ui/svg-icons/navigation/check'
import { fullWhite } from 'material-ui/styles/colors'
import { chatPropType } from '../utils/PropTypes'

class AnimatableContainer extends React.Component {
  constructor(props) {
    super(props)

    this.state = {
      style: props.beginStyle,
    }
  }

  componentWillUnmount() {
    clearTimeout(this.enterTimeout)
    clearTimeout(this.leaveTimeout)
  }

  componentWillEnter(callback) {
    this.componentWillAppear(callback)
  }

  componentWillAppear(callback) {
    // Timeout needed so that the component can render with the original styles
    // before we apply the ones to transition to
    setTimeout(() => {this.setState({
      style: this.props.endStyle
    })}, 0)

    this.enterTimeout = setTimeout(callback, 300)
  }

  componentWillLeave(callback) {
    this.setState({
      style: this.props.beginStyle,
    })

    this.leaveTimeout = setTimeout(callback, 300)
  }

  render() {
    const {
      style,
      children,
      ...other
    } = this.props

    return (
      <div {...other} style={Object.assign({}, style, this.state.style)}>
        {children}
      </div>
    )
  }
}

export default class ChatSelector extends React.Component {
  static propTypes = {
    chats: PropTypes.objectOf(chatPropType).isRequired,
    currentChat: PropTypes.string.isRequired,
    setTwitchChat: PropTypes.func.isRequired,
    open: PropTypes.bool.isRequired,
    onRequestClose: PropTypes.func.isRequired,
  }

  setTwitchChat(e, channel) {
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
      const isSelected = (chat.channel === this.props.currentChat)
      const icon = isSelected ? <CheckmarkIcon /> : null

      chatItems.push(
        <ListItem
          primaryText={chat.name}
          rightIcon={icon}
          onTouchTap={(e) => this.setTwitchChat(e, chat.channel)}
          key={chat.channel}
        />
      )
    })

    const overlayStyle = {
      width: '100%',
      height: '100%',
      background: 'rgba(0,0,0,0.2)',
      position: 'absolute',
      transition: 'all 150ms ease-in',
      willChange: 'opacity'
    }

    const listStyle = {
      width: '100%',
      position: 'absolute',
      bottom: 0,
      transition: 'all 150ms ease-in',
      willChange: 'transform opacity',
    }

    return (
      <ReactTransitionGroup
        component="div"
        transitionAppear={true}
        transitionAppearTimeout={150}
        transitionEnter={true}
        transitionEnterTimeout={150}
      >
        <div />
        {this.props.open &&
          <AnimatableContainer
            key="overlay"
            style={overlayStyle}
            onTouchTap={() => this.props.onRequestClose()}
            beginStyle={{
              opacity: 0,
            }}
            endStyle={{
              opacity: 1,
            }}
          />
        }
        {this.props.open &&
          <AnimatableContainer
            key="selector"
            style={listStyle}
            beginStyle={{
              opacity: 0,
              transform: 'translate(0, 50%)'
            }}
            endStyle={{
              opacity: 1,
              transform: 'translate(0, 0)'
            }}
          >
            <Paper zDepth={4}>
              <List onTouchTap={(e) => e.stopPropagation()}>
                {chatItems}
              </List>
            </Paper>
          </AnimatableContainer>
        }
      </ReactTransitionGroup>
    )
  }
}
