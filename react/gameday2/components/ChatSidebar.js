import React, { PropTypes } from 'react'
import muiThemeable from 'material-ui/styles/muiThemeable'
import IconButton from 'material-ui/IconButton'
import ArrowDropUp from 'material-ui/svg-icons/navigation/arrow-drop-up'
import { Toolbar, ToolbarGroup, ToolbarTitle } from 'material-ui/Toolbar'
import { white } from 'material-ui/styles/colors'
import ChatAnalyticsTracker from './ChatAnalyticsTracker'
import TwitchChatEmbed from './TwitchChatEmbed'
import ChatSelector from './ChatSelector'
import { chatPropType } from '../utils/PropTypes'

class ChatSidebar extends React.Component {
  static propTypes = {
    enabled: PropTypes.bool.isRequired,
    hasBeenVisible: PropTypes.bool.isRequired,
    chats: PropTypes.objectOf(chatPropType).isRequired,
    displayOrderChats: PropTypes.arrayOf(chatPropType).isRequired,
    renderedChats: PropTypes.arrayOf(PropTypes.string).isRequired,
    currentChat: PropTypes.string.isRequired,
    defaultChat: PropTypes.string.isRequired,
    setTwitchChat: PropTypes.func.isRequired,
    muiTheme: PropTypes.object.isRequired,
    setChatSidebarVisibility: PropTypes.object.isRequired,
    setHashtagSidebarVisibility: PropTypes.object.isRequired,
  }

  constructor(props) {
    super(props)

    this.state = {
      chatSelectorOpen: false,
    }

    this.onResize = this.onResize.bind(this)
  }

  componentDidMount() {
    this.onResize()
    window.addEventListener('resize', this.onResize)
  }

  onResize() {
    if (window.innerWidth < 760) {
      this.props.setChatSidebarVisibility(false)
      this.props.setHashtagSidebarVisibility(false)
    }
  }

  onRequestOpenChatSelector() {
    this.setState({
      chatSelectorOpen: true,
    })
  }

  onRequestCloseChatSelector() {
    this.setState({
      chatSelectorOpen: false,
    })
  }

  render() {
    const metrics = {
      switcherHeight: 36,
    }

    const panelContainerStyle = {
      position: 'absolute',
      top: this.props.muiTheme.layout.appBarHeight,
      right: 0,
      bottom: 0,
      width: this.props.muiTheme.layout.chatPanelWidth,
      background: '#EFEEF1',
      display: this.props.enabled ? null : 'none',
      zIndex: 1000,
    }

    const chatEmbedContainerStyle = {
      position: 'absolute',
      top: 0,
      bottom: metrics.switcherHeight,
      width: '100%',
    }

    const switcherToolbarStyle = {
      position: 'absolute',
      bottom: 0,
      height: metrics.switcherHeight,
      width: '100%',
      background: this.props.muiTheme.palette.primary1Color,
      cursor: 'pointer',
    }

    const toolbarTitleStyle = {
      color: white,
      fontSize: 16,
    }

    const toolbarButtonStyle = {
      width: metrics.switcherHeight,
      height: metrics.switcherHeight,
      padding: 8,
    }

    const toolbarButtonIconStyle = {
      width: (metrics.switcherHeight - 16),
      height: (metrics.switcherHeight - 16),
    }

    const renderedChats = []
    this.props.renderedChats.forEach((chat) => {
      const visible = (chat === this.props.currentChat)
      renderedChats.push(
        <TwitchChatEmbed
          channel={chat}
          key={chat}
          visible={visible}
        />
      )
    })

    const currentChat = this.props.chats[this.props.currentChat]
    let currentChatName = 'UNKNOWN'
    if (currentChat) {
      currentChatName = `${currentChat.name} Chat`
      if (currentChat.channel === 'firstupdatesnow' && this.props.defaultChat === 'firstupdatesnow') {
        currentChatName = 'TBA GameDay / FUN'
      } else if (currentChat.channel === 'firstinspires' && this.props.defaultChat === 'firstinspires') {
        currentChatName = 'TBA GameDay / FIRST'
      }
    }

    let content
    if (this.props.hasBeenVisible) {
      content = (
        <div style={panelContainerStyle}>
          <div style={chatEmbedContainerStyle}>
            {renderedChats}
          </div>
          <Toolbar
            style={switcherToolbarStyle}
            onTouchTap={() => this.onRequestOpenChatSelector()}
          >
            <ToolbarGroup>
              <ToolbarTitle
                text={currentChatName}
                style={toolbarTitleStyle}
              />
            </ToolbarGroup>
            <ToolbarGroup lastChild>
              <IconButton
                style={toolbarButtonStyle}
                iconStyle={toolbarButtonIconStyle}
              >
                <ArrowDropUp color={white} />
              </IconButton>
            </ToolbarGroup>
          </Toolbar>
          <ChatSelector
            chats={this.props.displayOrderChats}
            currentChat={this.props.currentChat}
            defaultChat={this.props.defaultChat}
            setTwitchChat={this.props.setTwitchChat}
            open={this.state.chatSelectorOpen}
            onRequestClose={() => this.onRequestCloseChatSelector()}
          />
          {this.props.enabled && <ChatAnalyticsTracker currentChat={this.props.currentChat} />}
        </div>
      )
    } else {
      content = (<div />)
    }

    return content
  }
}

export default muiThemeable()(ChatSidebar)
