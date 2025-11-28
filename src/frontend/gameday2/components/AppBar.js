import React from "react";
import Box from "@mui/material/Box";
import PropTypes from "prop-types";
import Toolbar from "@mui/material/Toolbar";
import IconButton from "@mui/material/IconButton";
import Button from "@mui/material/Button";
import { useTheme } from "@mui/material/styles";
import LayoutDrawer from "./LayoutDrawer";
import { getLayoutSvgIcon } from "../utils/layoutUtils";
import LampIcon from "./LampIcon";

const AppBar = (props) => {
  const theme = useTheme();

  const tbaBrandingButtonStyle = {
    padding: 0,
    marginLeft: 8,
    marginRight: 8,
    width: theme.layout.appBarHeight,
    height: theme.layout.appBarHeight,
  };

  const configureLayoutButtonStyle = {
    color: theme.appBar && theme.appBar.textColor,
  };

  const appBarStyle = {
    height: theme.layout.appBarHeight,
    minHeight: theme.layout.appBarHeight,
    backgroundColor:
      (theme.palette && theme.palette.primary && theme.palette.primary.main) ||
      undefined,
    zIndex: theme.zIndex && theme.zIndex.appBar,
    paddingRight: 0,
    paddingLeft: 0,
  };

  const appBarTitleStyle = {
    color: theme.appBar.textColor,
    fontSize: "24px",
    overflow: "visible",
  };

  const appBarSubtitleStyle = {
    color: theme.appBar.textColor,
    textDecoration: "none",
    fontSize: 12,
    paddingLeft: 8,
  };

  const tbaBrandingButton = (
    <IconButton
      style={tbaBrandingButtonStyle}
      href="https://www.thebluealliance.com"
    >
      <LampIcon
        width={theme.layout.appBarHeight}
        height={theme.layout.appBarHeight}
      />
    </IconButton>
  );

  const configureLayoutButton = (
    <Button
      startIcon={getLayoutSvgIcon(props.layoutId, "#ffffff")}
      style={configureLayoutButtonStyle}
      onClick={() => props.setLayoutDrawerVisibility(true)}
    >
      Configure Layout
    </Button>
  );

  return (
    <Box>
      <Toolbar
        style={appBarStyle}
        variant="dense"
        sx={{ flexDirection: "row", flexWrap: "nowrap" }}
      >
        {tbaBrandingButton}
        <Box sx={appBarTitleStyle}>GameDay</Box>
        <a style={appBarSubtitleStyle} href="/">
          by The Blue Alliance
        </a>
        <div
          className="fb-like"
          data-href="https://www.facebook.com/thebluealliance/"
          data-layout="button_count"
          data-action="like"
          data-size="small"
          data-show-faces="false"
          data-share="false"
        />
        <Box sx={{ marginLeft: "auto" }}>{configureLayoutButton}</Box>
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
    </Box>
  );
};

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
};

export default AppBar;
