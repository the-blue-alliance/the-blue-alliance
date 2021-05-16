import React from "react";
import muiThemeable from "material-ui/styles/muiThemeable";
import VideoGridContainer from "../containers/VideoGridContainer";
import LayoutSelectionPanel from "./LayoutSelectionPanel";
import NoWebcasts from "./NoWebcasts";

type Props = {
  webcasts: string[];
  hashtagSidebarVisible: boolean;
  chatSidebarVisible: boolean;
  layoutSet: boolean;
  setLayout: (...args: any[]) => any;
  muiTheme: any;
};

/**
 * Acts as a high-level "controller" for the main content area. This component
 * will render the appropriate child based on the state of the app. This will
 * also apply the appropriate margins to the main content area to position it
 * correctly when the sidebars are shown or hidden.
 *
 * If no webcasts are present, this displays a message for that.
 *
 * If webcasts are present but no layout is set, this displays a layout selector.
 *
 * If webcasts are present and a layout is set, this displays the video grid.
 */
const MainContent = (props: Props) => {
  let child = null;

  if (props.webcasts.length === 0) {
    // No webcasts. Do the thing!
    child = <NoWebcasts />;
  } else if (!props.layoutSet) {
    // No layout set. Display the layout selector.
    child = <LayoutSelectionPanel setLayout={props.setLayout} />;
  } else {
    // Display the video grid
    child = <VideoGridContainer />;
  }

  const contentStyles = {
    position: "absolute",
    top: props.muiTheme.layout.appBarHeight,
    left: 0,
    right: 0,
    bottom: 0,
    marginRight: props.chatSidebarVisible
      ? props.muiTheme.layout.chatPanelWidth
      : 0,
    marginLeft: props.hashtagSidebarVisible
      ? props.muiTheme.layout.socialPanelWidth
      : 0,
  };

  // @ts-expect-error ts-migrate(2322) FIXME: Type '{ position: string; top: any; left: number; ... Remove this comment to see the full error message
  return <div style={contentStyles}>{child}</div>;
};

// @ts-expect-error ts-migrate(2345) FIXME: Argument of type '(props: Props) => JSX.Element' i... Remove this comment to see the full error message
export default muiThemeable()(MainContent);
