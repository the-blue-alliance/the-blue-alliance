import { Button, IconButton, Toolbar } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import PropTypes from "prop-types";
import React from "react";
import { getLayoutSvgIcon } from "../utils/layoutUtils";
import LampIcon from "./LampIcon";
import LayoutDrawer from "./LayoutDrawer";

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
    color: theme.appBar.textColor,
  };

  const appBarStyle = {
    height: theme.layout.appBarHeight,
    backgroundColor: theme.palette.primary1Color,
    position: "relative",
    zIndex: theme.zIndex.appBar,
    paddingRight: 0,
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
  };

  const tbaBrandingButton = (
    <IconButton
      style={tbaBrandingButtonStyle}
      tooltip="Go to The Blue Alliance"
      tooltipPosition="bottom-right"
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
      label="Configure Layout"
      labelPosition="before"
      style={configureLayoutButtonStyle}
      icon={getLayoutSvgIcon(props.layoutId, "#ffffff")}
      onClick={() => props.setLayoutDrawerVisibility(true)}
    />
  );

  return (
    <div>
      <Toolbar style={appBarStyle}>
        <ToolbarGroup firstChild>
          {tbaBrandingButton}
          <ToolbarTitle text="GameDay" style={appBarTitleStyle} />
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
        </ToolbarGroup>
        <ToolbarGroup lastChild>{configureLayoutButton}</ToolbarGroup>
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
  muiTheme: PropTypes.object.isRequired,
};

export default AppBar;
