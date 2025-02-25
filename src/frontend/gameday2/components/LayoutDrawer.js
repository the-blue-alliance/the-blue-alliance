import React from "react";
import PropTypes from "prop-types";
import { withTheme } from '@mui/styles';
import Button from "@mui/material/Button";
import Drawer from "@mui/material/Drawer";
import Divider from "@mui/material/Divider";
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListSubheader from '@mui/material/ListSubheader';
import Switch from '@mui/material/Switch';
import { red } from "@mui/material/colors";
import CheckIcon from '@mui/icons-material/Check';
import { getLayoutSvgIcon } from "../utils/layoutUtils";
import {
  NUM_LAYOUTS,
  LAYOUT_DISPLAY_ORDER,
  NAME_FOR_LAYOUT,
} from "../constants/LayoutConstants";

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
    theme: PropTypes.object.isRequired,
  };

  handleResetWebcasts() {
    this.props.resetWebcasts();
  }

  render() {
    // If there aren't any webcasts, display a message instead
    // of unselectable checkboxes
    const layouts = [];
    if (this.props.hasWebcasts) {
      for (let i = 0; i < NUM_LAYOUTS; i++) {
        const layoutNum = LAYOUT_DISPLAY_ORDER[i];
        const showCheck =
          layoutNum === this.props.selectedLayout && this.props.layoutSet;
        const icon = showCheck ? <CheckIcon /> : null;

        layouts.push(
          <ListItem
            primaryText={NAME_FOR_LAYOUT[layoutNum]}
            insetChildren
            onClick={() => this.props.setLayout(layoutNum)}
            key={i.toString()}
            rightIcon={icon}
            leftIcon={getLayoutSvgIcon(layoutNum)}
          />
        );
      }
    } else {
      layouts.push(
        <ListItem
          primaryText="There aren't any webcasts available right now. Check back later!"
          key="empty"
          disabled
        />
      );
    }

    const chatToggle = (
      <Switch
        onChange={() => this.props.toggleChatSidebarVisibility()}
        checked={this.props.chatSidebarVisible}
      />
    );

    const hashtagToggle = (
      <Switch
        onChange={() => this.props.toggleHashtagSidebarVisibility()}
        checked={this.props.hashtagSidebarVisible}
      />
    );

    const primaryColor = this.props.theme.palette.primary1Color;

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
            <ListSubheader style={{ color: primaryColor }}>
              Select video grid layout
            </ListSubheader>
            {layouts}
          </List>
          <Divider />
          <List>
            <ListSubheader style={{ color: primaryColor }}>
              Enable/disable sidebars
            </ListSubheader>
            <ListItem
              primaryText="Social Sidebar"
              rightToggle={hashtagToggle}
            />
            <ListItem primaryText="Chat Sidebar" rightToggle={chatToggle} />
          </List>
          <Divider />
          <div style={{ padding: 8 }}>
            <Button
              variant="contained"
              label="Reset Webcasts"
              backgroundColor={red[500]}
              labelColor='white'
              fullWidth
              onClick={() => this.handleResetWebcasts()}
            />
          </div>
        </div>
      </Drawer>
    );
  }
}

export default withTheme(LayoutDrawer);
