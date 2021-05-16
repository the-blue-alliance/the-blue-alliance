import React from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import { Toolbar, ToolbarTitle, ToolbarGroup } from "material-ui/Toolbar";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import FlatButton from "material-ui/FlatButton";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import IconButton from "material-ui/IconButton";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import muiThemeable from "material-ui/styles/muiThemeable";
import LayoutDrawer from "./LayoutDrawer";
import { getLayoutSvgIcon } from "../utils/layoutUtils";
import LampIcon from "./LampIcon";

type Props = {
  webcasts: string[];
  hashtagSidebarVisible: boolean;
  chatSidebarVisible: boolean;
  resetWebcasts: (...args: any[]) => any;
  toggleHashtagSidebarVisibility: (...args: any[]) => any;
  toggleChatSidebarVisibility: (...args: any[]) => any;
  setLayout: (...args: any[]) => any;
  layoutId: number;
  layoutSet: boolean;
  layoutDrawerVisible: boolean;
  setLayoutDrawerVisibility: (...args: any[]) => any;
  muiTheme: any;
};

const AppBar = (props: Props) => {
  const tbaBrandingButtonStyle = {
    padding: 0,
    marginLeft: 8,
    marginRight: 8,
    width: props.muiTheme.layout.appBarHeight,
    height: props.muiTheme.layout.appBarHeight,
  };

  const configureLayoutButtonStyle = {
    color: props.muiTheme.appBar.textColor,
  };

  const appBarStyle = {
    height: props.muiTheme.layout.appBarHeight,
    backgroundColor: props.muiTheme.palette.primary1Color,
    position: "relative",
    zIndex: props.muiTheme.zIndex.appBar,
    paddingRight: 0,
  };

  const appBarTitleStyle = {
    color: props.muiTheme.appBar.textColor,
    fontSize: "24px",
    overflow: "visible",
  };

  const appBarSubtitleStyle = {
    color: props.muiTheme.appBar.textColor,
    textDecoration: "none",
    fontSize: 12,
  };

  const vexProStyle = {
    color: props.muiTheme.appBar.textColor,
    textDecoration: "none",
    marginLeft: 32,
    marginRight: 64,
    fontSize: 12,
    display: "flex",
    alignItems: "center",
  };

  const tbaBrandingButton = (
    <IconButton
      style={tbaBrandingButtonStyle}
      tooltip="Go to The Blue Alliance"
      tooltipPosition="bottom-right"
      href="https://www.thebluealliance.com"
    >
      <LampIcon
        width={props.muiTheme.layout.appBarHeight}
        height={props.muiTheme.layout.appBarHeight}
      />
    </IconButton>
  );

  const configureLayoutButton = (
    <FlatButton
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
          <a style={vexProStyle} href="https://www.vexrobotics.com/vexpro/">
            <span style={{ marginRight: "4px" }}>POWERED BY</span>
            <img src="/images/vexpro_horiz.png" alt="vexPRO" height={16} />
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

export default muiThemeable()(AppBar);
