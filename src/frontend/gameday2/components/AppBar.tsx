import React from "react";
import { Toolbar, ToolbarTitle, ToolbarGroup } from "material-ui/Toolbar";
import FlatButton from "material-ui/FlatButton";
import IconButton from "material-ui/IconButton";
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
      {/* @ts-expect-error ts-migrate(2769) FIXME: No overload matches this call. */}
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
        // @ts-expect-error ts-migrate(2322) FIXME: Type '{ setLayout: (...args: any[]) => any; toggle... Remove this comment to see the full error message
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

// @ts-expect-error ts-migrate(2345) FIXME: Argument of type '(props: Props) => JSX.Element' i... Remove this comment to see the full error message
export default muiThemeable()(AppBar);
