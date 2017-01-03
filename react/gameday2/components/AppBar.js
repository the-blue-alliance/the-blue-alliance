import React, { PropTypes } from 'react'
import MuiAppBar from 'material-ui/AppBar'
import { Toolbar, ToolbarTitle, ToolbarGroup } from 'material-ui/Toolbar'
import FlatButton from 'material-ui/FlatButton'
import IconButton from 'material-ui/IconButton'
import muiThemeable from 'material-ui/styles/muiThemeable'
import LayoutDrawer from './LayoutDrawer'
import { getLayoutSvgIcon } from '../utils/layoutUtils'
import LampIcon from './LampIcon'

const AppBar = (props) => {
  const tbaBrandingButtonStyle = {
    padding: 0,
    marginLeft: 8,
    marginRight: 8,
  }

  const configureLayoutButtonStyle = {
    color: props.muiTheme.appBar.textColor,
  }

  const appBarStyle = {
    height: props.muiTheme.layout.appBarHeight,
    backgroundColor: props.muiTheme.palette.primary1Color,
    position: 'relative',
    zIndex: props.muiTheme.zIndex.appBar,
  }

  const appBarTitleStyle = {
    color: props.muiTheme.appBar.textColor,
    fontSize: '24px',
  }

  const tbaBrandingButton = (
    <IconButton
      style={tbaBrandingButtonStyle}
      tooltip="Go to The Blue Alliance"
      tooltipPosition="bottom-right"
      href="https://thebluealliance.com"
    >
      <LampIcon
        width={props.muiTheme.layout.appBarHeight - 16}
        height={props.muiTheme.layout.appBarHeight - 16}
      />
    </IconButton>
  )

  const configureLayoutButton = (
    <FlatButton
      label="Configure Layout"
      labelPosition="before"
      style={configureLayoutButtonStyle}
      icon={getLayoutSvgIcon(props.layoutId, '#ffffff')}
      onTouchTap={() => props.setLayoutDrawerVisibility(true)}
    />
  )

  return (
    <div>
      <Toolbar
        style={appBarStyle}
      >
        <ToolbarGroup firstChild>
          {tbaBrandingButton}
          <ToolbarTitle text="GameDay" style={appBarTitleStyle} />
        </ToolbarGroup>
        <ToolbarGroup lastChild>
          {configureLayoutButton}
        </ToolbarGroup>
      </Toolbar>
      <LayoutDrawer
        setLayout={props.setLayout}
        toggleChatSidebarVisibility={props.toggleChatSidebarVisibility}
        toggleHashtagSidebarVisibility={props.toggleHashtagSidebarVisibility}
        selectedLayout={props.layoutId}
        layoutSet={props.layoutSet}
        chatSidebarVisible={props.chatSidebarVisible}
        hashtagSidebarVisible={props.hashtagSidebarVisible}
        layoutDrawerVisible={props.layoutDrawerVisible}
        setLayoutDrawerVisibility={props.setLayoutDrawerVisibility}
        hasWebcasts={props.webcasts.length > 0}
        resetWebcasts={props.resetWebcasts}
      />
    </div>
  )
}

AppBar.propTypes = {
  webcasts: PropTypes.arrayOf(PropTypes.string).isRequired,
  hashtagSidebarVisible: PropTypes.bool.isRequired,
  chatSidebarVisible: PropTypes.bool.isRequired,
  resetWebcasts: PropTypes.func.isRequired,
  toggleHashtagSidebarVisibility: PropTypes.func.isRequired,
  toggleChatSidebarVisibility: PropTypes.func.isRequired,
  setLayout: PropTypes.func.isRequired,
  layoutId: PropTypes.number.isRequired,
  layoutSet: PropTypes.bool.isRequired,
  layoutDrawerVisible: PropTypes.bool.isRequired,
  setLayoutDrawerVisibility: PropTypes.func.isRequired,
  muiTheme: PropTypes.object.isRequired,
}

export default muiThemeable()(AppBar)
