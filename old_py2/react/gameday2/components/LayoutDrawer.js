import React, { PropTypes } from 'react'
import muiThemeable from 'material-ui/styles/muiThemeable'
import RaisedButton from 'material-ui/RaisedButton'
import Drawer from 'material-ui/Drawer'
import Divider from 'material-ui/Divider'
import { List, ListItem } from 'material-ui/List'
import Subheader from 'material-ui/Subheader'
import Toggle from 'material-ui/Toggle'
import { red500, fullWhite } from 'material-ui/styles/colors'
import CheckmarkIcon from 'material-ui/svg-icons/navigation/check'
import { getLayoutSvgIcon } from '../utils/layoutUtils'
import { NUM_LAYOUTS, LAYOUT_DISPLAY_ORDER, NAME_FOR_LAYOUT } from '../constants/LayoutConstants'

class LayoutDrawer extends React.Component {
  static propTypes = {
    setLayout: PropTypes.func.isRequired,
    selectedLayout: PropTypes.number.isRequired,
    layoutSet: PropTypes.bool.isRequired,
    hashtagSidebarVisible: PropTypes.bool.isRequired,
    chatSidebarVisible: PropTypes.bool.isRequired,
    layoutDrawerVisible: PropTypes.bool.isRequired,
    setLayoutDrawerVisibility: PropTypes.func.isRequired,
    hasWebcasts: PropTypes.bool.isRequired,
    toggleChatSidebarVisibility: PropTypes.func.isRequired,
    toggleHashtagSidebarVisibility: PropTypes.func.isRequired,
    resetWebcasts: PropTypes.func.isRequired,
    muiTheme: PropTypes.object.isRequired,
  }

  handleResetWebcasts() {
    this.props.resetWebcasts()
  }

  render() {
    // If there aren't any webcasts, display a message instead
    // of unselectable checkboxes
    const layouts = []
    if (this.props.hasWebcasts) {
      for (let i = 0; i < NUM_LAYOUTS; i++) {
        const layoutNum = LAYOUT_DISPLAY_ORDER[i]
        const showCheck = (layoutNum === this.props.selectedLayout && this.props.layoutSet)
        const icon = showCheck ? <CheckmarkIcon /> : null

        layouts.push(
          <ListItem
            primaryText={NAME_FOR_LAYOUT[layoutNum]}
            insetChildren
            onTouchTap={() => this.props.setLayout(layoutNum)}
            key={i.toString()}
            rightIcon={icon}
            leftIcon={getLayoutSvgIcon(layoutNum)}
          />
        )
      }
    } else {
      layouts.push(
        <ListItem
          primaryText="There aren't any webcasts available right now. Check back later!"
          key="empty"
          disabled
        />
      )
    }

    const chatToggle = (
      <Toggle
        onToggle={() => this.props.toggleChatSidebarVisibility()}
        toggled={this.props.chatSidebarVisible}
      />
    )

    const hashtagToggle = (
      <Toggle
        onToggle={() => this.props.toggleHashtagSidebarVisibility()}
        toggled={this.props.hashtagSidebarVisible}
      />
    )

    const primaryColor = this.props.muiTheme.palette.primary1Color

    return (
      <Drawer
        docked={false}
        open={this.props.layoutDrawerVisible}
        onRequestChange={(open) => this.props.setLayoutDrawerVisibility(open)}
        openSecondary
        width={300}
      >
        <div>
          <List>
            <Subheader style={{ color: primaryColor }}>Select video grid layout</Subheader>
            {layouts}
          </List>
          <Divider />
          <List>
            <Subheader style={{ color: primaryColor }}>Enable/disable sidebars</Subheader>
            <ListItem
              primaryText="Social Sidebar"
              rightToggle={hashtagToggle}
            />
            <ListItem
              primaryText="Chat Sidebar"
              rightToggle={chatToggle}
            />
          </List>
          <Divider />
          <div style={{ padding: 8 }}>
            <RaisedButton
              label="Reset Webcasts"
              backgroundColor={red500}
              labelColor={fullWhite}
              fullWidth
              onTouchTap={() => this.handleResetWebcasts()}
            />
          </div>
        </div>
      </Drawer>
    )
  }
}

export default muiThemeable()(LayoutDrawer)
