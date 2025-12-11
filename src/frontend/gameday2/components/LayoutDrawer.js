import React from "react";
import PropTypes from "prop-types";
import { useTheme } from "@mui/material/styles";
import Button from "@mui/material/Button";
import Drawer from "@mui/material/Drawer";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemSecondaryAction from "@mui/material/ListItemSecondaryAction";
import ListSubheader from "@mui/material/ListSubheader";
import Switch from "@mui/material/Switch";
import { red, common } from "@mui/material/colors";
import CheckIcon from "@mui/icons-material/Check";
import { getLayoutSvgIcon } from "../utils/layoutUtils";
import {
  NUM_LAYOUTS,
  LAYOUT_DISPLAY_ORDER,
  NAME_FOR_LAYOUT,
} from "../constants/LayoutConstants";

const LayoutDrawer = (props) => {
  const theme = useTheme();

  // If there aren't any webcasts, display a message instead of unselectable checkboxes
  const layouts = [];
  if (props.hasWebcasts) {
    for (let i = 0; i < NUM_LAYOUTS; i++) {
      const layoutNum = LAYOUT_DISPLAY_ORDER[i];
      const showCheck = layoutNum === props.selectedLayout && props.layoutSet;
      const icon = showCheck ? <CheckIcon /> : null;

      layouts.push(
        <ListItem
          button
          onClick={() => props.setLayout(layoutNum)}
          key={i.toString()}
        >
          <ListItemIcon>{getLayoutSvgIcon(layoutNum)}</ListItemIcon>
          <ListItemText primary={NAME_FOR_LAYOUT[layoutNum]} />
          <ListItemSecondaryAction>{icon}</ListItemSecondaryAction>
        </ListItem>
      );
    }
  } else {
    layouts.push(
      <ListItem key="empty" disabled>
        <ListItemText
          primary={
            "There aren't any webcasts available right now. Check back later!"
          }
        />
      </ListItem>
    );
  }

  const chatToggle = (
    <Switch
      onChange={() => props.toggleChatSidebarVisibility()}
      checked={props.chatSidebarVisible}
    />
  );

  const hashtagToggle = (
    <Switch
      onChange={() => props.toggleHashtagSidebarVisibility()}
      checked={props.hashtagSidebarVisible}
    />
  );

  const primaryColor =
    (theme.palette && theme.palette.primary && theme.palette.primary.main) ||
    undefined;

  return (
    <Drawer
      open={props.layoutDrawerVisible}
      onClose={() => props.setLayoutDrawerVisibility(false)}
      anchor="right"
      PaperProps={{
        style: { width: 300, marginTop: theme.layout.appBarHeight },
      }}
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
          <ListItem>
            <ListItemText primary="Social Sidebar" />
            <ListItemSecondaryAction>{hashtagToggle}</ListItemSecondaryAction>
          </ListItem>
          <ListItem>
            <ListItemText primary="Chat Sidebar" />
            <ListItemSecondaryAction>{chatToggle}</ListItemSecondaryAction>
          </ListItem>
        </List>
        <Divider />
        <div style={{ padding: 8 }}>
          <Button
            variant="contained"
            fullWidth
            onClick={() => props.resetWebcasts()}
            style={{ backgroundColor: red[500], color: common.white }}
          >
            Reset Webcasts
          </Button>
        </div>
      </div>
    </Drawer>
  );
};

LayoutDrawer.propTypes = {
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
};

export default LayoutDrawer;
