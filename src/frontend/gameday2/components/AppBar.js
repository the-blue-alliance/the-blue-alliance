import React from "react";
import PropTypes from "prop-types";
import Toolbar from "@mui/material/Toolbar";
import Typography from '@mui/material/Typography';
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";
import { withTheme } from '@mui/styles';
import LayoutDrawer from "./LayoutDrawer";
import { getLayoutSvgIcon } from "../utils/layoutUtils";
import LampIcon from "./LampIcon";

const AppBar = (props) => {
  const tbaBrandingButtonStyle = {
    padding: 0,
    marginLeft: 8,
    marginRight: 8,
    width: props.theme.layout.appBarHeight,
    height: props.theme.layout.appBarHeight,
  };

  /*
  const configureLayoutButtonStyle = {
    color: props.theme.appBar.textColor,
  };
  */

  /*
  const appBarStyle = {
    height: props.theme.layout.appBarHeight,
    backgroundColor: props.theme.palette.primary1Color,
    position: "relative",
    zIndex: props.theme.zIndex.appBar,
    paddingRight: 0,
  };
  */

  /*
  const appBarTitleStyle = {
    color: props.theme.appBar.textColor,
    fontSize: "24px",
    overflow: "visible",
  };
  */

  /*
  const appBarSubtitleStyle = {
    color: props.theme.appBar.textColor,
    textDecoration: "none",
    fontSize: 12,
  };
  */

  const tbaBrandingButton = (
    <IconButton
      style={tbaBrandingButtonStyle}
      tooltip="Go to The Blue Alliance"
      tooltipposition="bottom-right"
      href="https://www.thebluealliance.com"
    >
      <LampIcon
        width={props.theme.layout.appBarHeight}
        height={props.theme.layout.appBarHeight}
      />
    </IconButton>
  );

  const configureLayoutButton = (
    <Button
      label="Configure Layout"
      icon={getLayoutSvgIcon(props.layoutId, "#ffffff")}
      onClick={() => props.setLayoutDrawerVisibility(true)}
    />
  );

  return (
    <div>
      <Toolbar>
          {tbaBrandingButton}
          <Typography>GameDay</Typography>
          <a href="/">
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
        {configureLayoutButton}
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
  theme: PropTypes.object.isRequired,
};

export default withTheme(AppBar);
