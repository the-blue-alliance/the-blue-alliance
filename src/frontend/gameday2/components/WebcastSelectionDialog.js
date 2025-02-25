import React from "react";
import PropTypes from "prop-types";
import Dialog from "@mui/material/Dialog";
import { green, indigo } from "@mui/material/colors";
import Divider from "@mui/material/Divider";
import Button from "@mui/material/Button";
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListSubheader from "@mui/material/ListSubheader";
import GradeIcon from '@mui/icons-material/Grade';
import HelpIcon from '@mui/icons-material/Help';
import VideocamIcon from '@mui/icons-material/Videocam';
import VideocamOffIcon from '@mui/icons-material/VideocamOff';
import WebcastSelectionDialogItem from "./WebcastSelectionDialogItem";
import { webcastPropType } from "../utils/webcastUtils";

export default class WebcastSelectionDialog extends React.Component {
  static propTypes = {
    open: PropTypes.bool.isRequired,
    webcasts: PropTypes.arrayOf(PropTypes.string).isRequired,
    webcastsById: PropTypes.objectOf(webcastPropType).isRequired,
    specialWebcastIds: PropTypes.any.isRequired, // Can't figure out how to check for Set()
    displayedWebcasts: PropTypes.arrayOf(PropTypes.string).isRequired,
    onWebcastSelected: PropTypes.func.isRequired,
    onRequestClose: PropTypes.func.isRequired,
  };

  onRequestClose() {
    if (this.props.onRequestClose) {
      this.props.onRequestClose();
    }
  }

  render() {
    const subheaderStyle = {
      color: indigo[500],
    };

    // Construct list of webcasts
    const bluezoneWebcastItems = [];
    const specialWebcastItems = [];
    const webcastItems = [];
    const offlineSpecialWebcastItems = [];
    const offlineWebcastItems = [];
    // Don't let the user choose a webcast that is already displayed elsewhere
    const availableWebcasts = this.props.webcasts.filter(
      (webcastId) => this.props.displayedWebcasts.indexOf(webcastId) === -1
    );
    availableWebcasts.forEach((webcastId) => {
      const webcast = this.props.webcastsById[webcastId];

      let rightIcon = <HelpIcon />;
      let secondaryText = null;
      if (webcast.status === "online") {
        rightIcon = (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "flex-end",
              width: 96,
            }}
          >
            {webcast.viewerCount && (
              <small
                style={{
                  textAlign: "center",
                  marginRight: 8,
                }}
              >
                {webcast.viewerCount.toLocaleString()}
                <br />
                Viewers
              </small>
            )}
            <VideocamIcon color={green[500]} />
          </div>
        );
        if (webcast.streamTitle) {
          secondaryText = webcast.streamTitle;
        }
      } else if (webcast.status === "offline") {
        rightIcon = <VideocamOffIcon />;
      }

      if (this.props.specialWebcastIds.has(webcast.id)) {
        const item = (
          <WebcastSelectionDialogItem
            key={webcast.id}
            webcast={webcast}
            webcastSelected={this.props.onWebcastSelected}
            secondaryText={secondaryText}
            rightIcon={rightIcon}
          />
        );
        if (webcast.status === "offline") {
          offlineSpecialWebcastItems.push(item);
        } else {
          specialWebcastItems.push(item);
        }
      } else if (webcast.id.startsWith("bluezone")) {
        bluezoneWebcastItems.push(
          <WebcastSelectionDialogItem
            key={webcast.id}
            webcast={webcast}
            webcastSelected={this.props.onWebcastSelected}
            secondaryText={"The best matches from across FRC"}
            rightIcon={<GradeIcon color={indigo[500]} />}
          />
        );
      } else {
        const item = (
          <WebcastSelectionDialogItem
            key={webcast.id}
            webcast={webcast}
            webcastSelected={this.props.onWebcastSelected}
            secondaryText={secondaryText}
            rightIcon={rightIcon}
          />
        );
        if (webcast.status === "offline") {
          offlineWebcastItems.push(item);
        } else {
          webcastItems.push(item);
        }
      }
    });

    let allWebcastItems = [];
    if (specialWebcastItems.length !== 0 || bluezoneWebcastItems.length !== 0) {
      allWebcastItems.push(
        <ListSubheader key="specialWebcastsHeader" style={subheaderStyle}>
          Special Webcasts
        </ListSubheader>
      );
      allWebcastItems = allWebcastItems.concat(bluezoneWebcastItems);
      allWebcastItems = allWebcastItems.concat(specialWebcastItems);
    }
    if (webcastItems.length !== 0) {
      if (specialWebcastItems.length !== 0) {
        allWebcastItems.push(<Divider key="eventWebcastsDivider" />);
      }
      allWebcastItems.push(
        <ListSubheader key="eventWebcastsHeader" style={subheaderStyle}>
          Event Webcasts
        </ListSubheader>
      );
      allWebcastItems = allWebcastItems.concat(webcastItems);
    }
    if (offlineWebcastItems.length !== 0) {
      if (webcastItems.length !== 0) {
        allWebcastItems.push(<Divider key="offlineEventWebcastsDivider" />);
      }
      allWebcastItems.push(
        <ListSubheader key="offlineWebcastsHeader" style={subheaderStyle}>
          Offline Event Webcasts
        </ListSubheader>
      );
      allWebcastItems = allWebcastItems.concat(offlineWebcastItems);
    }
    if (offlineSpecialWebcastItems.length !== 0) {
      if (offlineWebcastItems.length !== 0) {
        allWebcastItems.push(<Divider key="offlineSpecialWebcastsDivider" />);
      }
      allWebcastItems.push(
        <ListSubheader key="offlineSpecialWebcastsHeader" style={subheaderStyle}>
          Offline Special Webcasts
        </ListSubheader>
      );
      allWebcastItems = allWebcastItems.concat(offlineSpecialWebcastItems);
    }

    if (allWebcastItems.length === 0) {
      // No more webcasts, indicate that
      allWebcastItems.push(
        <ListItem
          key="nullWebcastsListItem"
          primaryText="No more webcasts available"
          disabled
        />
      );
    }

    const actions = [
      <Button
        label="Cancel"
        onClick={() => this.onRequestClose()}
        primary
      />,
    ];

    const titleStyle = {
      padding: 16,
    };

    const bodyStyle = {
      padding: 0,
    };

    return (
      <Dialog
        title="Select a webcast"
        actions={actions}
        modal={false}
        titleStyle={titleStyle}
        bodyStyle={bodyStyle}
        open={this.props.open}
        onRequestClose={() => this.onRequestClose()}
        autoScrollBodyContent
      >
        <List>{allWebcastItems}</List>
      </Dialog>
    );
  }
}
