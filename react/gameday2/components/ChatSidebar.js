import React, { PropTypes } from 'react'
import muiThemeable from 'material-ui/styles/muiThemeable'
import IconButton from 'material-ui/IconButton'
import ArrowDropUp from 'material-ui/svg-icons/navigation/arrow-drop-up'
import { Toolbar, ToolbarGroup, ToolbarTitle } from 'material-ui/Toolbar'
import { white } from 'material-ui/styles/colors'
import TwitchChatEmbed from './TwitchChatEmbed'

const ChatSidebar = (props) => {

  const metrics = {
    switcherHeight: 48,
  }

  const panelContainerStyle = {
    position: 'absolute',
    top: props.muiTheme.layout.appBarHeight,
    right: 0,
    bottom: 0,
    width: props.muiTheme.layout.chatPanelWidth,
    background: '#EFEEF1',
    display: props.enabled ? null : 'none',
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
    background: props.muiTheme.palette.primary1Color,
  }

  const toolbarTitleStyle = {
    color: white,
    fontSize: 16,
  }

  let content
  if (props.hasBeenVisible) {
    content = (
      <div style={panelContainerStyle}>
        <div style={chatEmbedContainerStyle}>
          <TwitchChatEmbed
            channel="tbagameday"
            visible
          />
        </div>
        <Toolbar style={switcherToolbarStyle}>
          <ToolbarGroup>
            <ToolbarTitle
              text="Hello!"
              style={toolbarTitleStyle}
            />
          </ToolbarGroup>
          <ToolbarGroup lastChild>
            <IconButton>
              <ArrowDropUp color={white} />
            </IconButton>
          </ToolbarGroup>
        </Toolbar>
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

export default muiThemeable()(ChatSidebar)
