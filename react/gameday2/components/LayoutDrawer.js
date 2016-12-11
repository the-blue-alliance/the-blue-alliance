import React, { PropTypes } from 'react'
import RaisedButton from 'material-ui/RaisedButton'
import Drawer from 'material-ui/Drawer'
import Divider from 'material-ui/Divider'
import { List, ListItem } from 'material-ui/List'
import Subheader from 'material-ui/Subheader'
import Toggle from 'material-ui/Toggle'
import { red500, fullWhite } from 'material-ui/styles/colors'
import CheckmarkIcon from 'material-ui/svg-icons/navigation/check'
import { NUM_LAYOUTS, NUM_VIEWS_FOR_LAYOUT, NAME_FOR_LAYOUT } from '../constants/LayoutConstants'

export default class LayoutDrawer extends React.Component {
  static propTypes = {
    setLayout: PropTypes.func.isRequired,
    resetLayout: PropTypes.func.resetLayout,
    selectedLayout: PropTypes.number.isRequired,
    layoutSet: PropTypes.bool.isRequired,
    hashtagSidebarVisible: PropTypes.bool.isRequired,
    chatSidebarVisible: PropTypes.bool.isRequired,
    layoutDrawerVisible: PropTypes.bool.isRequired,
    setLayoutDrawerVisibility: PropTypes.func.isRequired,
    hasWebcasts: PropTypes.bool.isRequired,
    toggleChatSidebarVisibility: PropTypes.func.isRequired,
    toggleHashtagSidebarVisibility: PropTypes.func.isRequired,
  }

  constructor(props) {
    super(props)
  }

  handleResetWebcasts() {
    this.props.resetWebcasts()
  }

  render() {
    // If there aren't any webcasts, display a message instead
    // of unselectable checkboxes
    let layouts = []
    if (this.props.hasWebcasts) {
      for (let i = 0; i < NUM_LAYOUTS; i++) {
        const icon = (i == this.props.selectedLayout && this.props.layoutSet) ? <CheckmarkIcon /> : null

        layouts.push(
          <ListItem
            primaryText={NAME_FOR_LAYOUT[i]}
            insetChildren={true}
            onTouchTap={() => this.props.setLayout(i)}
            key={i.toString()}
            leftIcon={icon}
          />
        )
      }
    } else {
      layouts.push(
        <ListItem
          primaryText="There aren't any webcasts available right now. Check back later!"
          disabled={true}
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

    return (
      <Drawer
        docked={false}
        open={this.props.layoutDrawerVisible}
        onRequestChange={(open) => this.props.setLayoutDrawerVisibility(open)}
        openSecondary={true}
        width={300}
      >
        <div>
          <List>
            <Subheader>Select video grid layout</Subheader>
            {layouts}
          </List>
          <Divider />
          <List>
            <Subheader>Enable/disable sidebars</Subheader>
            <ListItem
              primaryText='Social Sidebar'
              rightToggle={hashtagToggle}
            />
            <ListItem
              primaryText='Chat Sidebar'
              rightToggle={chatToggle}
            />
          </List>
          <Divider />
          <div style={{padding: 8}}>
            <RaisedButton
              label='Reset Webcasts'
              backgroundColor={red500}
              labelColor={fullWhite}
              fullWidth={true}
              onTouchTap={() => this.handleResetWebcasts()}
            />
          </div>
        </div>
      </Drawer>
    )
  }
}
