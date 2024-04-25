import { useTheme } from "@mui/material/styles";
import PropTypes from "prop-types";
import React from "react";
import VideoGridContainer from "../containers/VideoGridContainer";
import LayoutSelectionPanel from "./LayoutSelectionPanel";
import NoWebcasts from "./NoWebcasts";

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
const MainContent = (props) => {
  const theme = useTheme();

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
    top: theme.layout.appBarHeight,
    left: 0,
    right: 0,
    bottom: 0,
    marginRight: props.chatSidebarVisible ? theme.layout.chatPanelWidth : 0,
    marginLeft: props.hashtagSidebarVisible ? theme.layout.socialPanelWidth : 0,
  };

  return <div style={contentStyles}>{child}</div>;
};

MainContent.propTypes = {
  webcasts: PropTypes.arrayOf(PropTypes.string).isRequired,
  hashtagSidebarVisible: PropTypes.bool.isRequired,
  chatSidebarVisible: PropTypes.bool.isRequired,
  layoutSet: PropTypes.bool.isRequired,
  setLayout: PropTypes.func.isRequired,
  muiTheme: PropTypes.object.isRequired,
};

export default MainContent;
