import React, { PropTypes } from 'react'
import AppBar from 'material-ui/AppBar'
import FlatButton from 'material-ui/FlatButton'
import muiThemeable from 'material-ui/styles/muiThemeable'
import LayoutDrawer from './LayoutDrawer'
import { getLayoutSvgIcon } from '../utils/layoutUtils'

const GamedayNavbar = (props) => {
  const configureLayoutButton = (
    <FlatButton
      label="Configure Layout"
      labelPosition="before"
      icon={getLayoutSvgIcon(props.layoutId, '#ffffff')}
      onTouchTap={() => props.setLayoutDrawerVisibility(true)}
    />
  )

  const appBarStyle = {
    height: props.muiTheme.layout.appBarHeight,
  }

  return (
    <div>
      <AppBar
        style={appBarStyle}
        title="GameDay"
        showMenuIconButton={false}
        iconElementRight={configureLayoutButton}
      />
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

GamedayNavbar.propTypes = {
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
}

export default muiThemeable()(GamedayNavbar)
