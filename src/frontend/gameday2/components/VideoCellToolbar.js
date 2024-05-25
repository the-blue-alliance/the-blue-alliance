import React from "react";
import PropTypes from "prop-types";
import { Toolbar, ToolbarGroup } from "material-ui/Toolbar";
import FlatButton from "material-ui/FlatButton";
import IconButton from "material-ui/IconButton";
import CloseIcon from "material-ui/svg-icons/navigation/close";
import SwapIcon from "material-ui/svg-icons/action/compare-arrows";
import VideocamIcon from "material-ui/svg-icons/av/videocam";
import EqualizerIcon from "material-ui/svg-icons/av/equalizer";
import { white, green500, grey900 } from "material-ui/styles/colors";

import TickerMatch from "./TickerMatch";
import { NUM_VIEWS_FOR_LAYOUT } from "../constants/LayoutConstants";

const VideoCellToolbar = (props) => {
  const toolbarStyle = {
    backgroundColor: grey900,
    ...props.style,
  };

  const titleStyle = {
    color: white,
    fontSize: 16,
    marginLeft: 0,
    marginRight: 0,
  };

  const matchTickerGroupStyle = {
    flexGrow: 1,
    width: "0%", // Slightly hacky. Prevents ticker from bleeding into next cell
    overflow: "hidden",
    whiteSpace: "nowrap",
  };

  const matchTickerStyle = {
    overflow: "hidden",
    whiteSpace: "nowrap",
  };

  const controlsStyle = {
    position: "absolute",
    right: 0,
    marginRight: 0,
    backgroundColor: grey900,
    boxShadow: "-2px 0px 15px -2px rgba(0, 0, 0, 0.5)",
  };

  // Create tickerMatches
  const tickerMatches = [];
  props.matches.forEach((match) => {
    if (match.rt && match.rt.length > 0 && match.bt && match.bt.length > 0) {
      // 2024 Week 3, FMS Sync issues result in schedules
      // being posted without teams, so skip those matchesk

      // See if match has a favorite team
      let hasFavorite = false;
      const teamKeys = match.rt.concat(match.bt);
      teamKeys.forEach((teamKey) => {
        if (props.favoriteTeams.has(teamKey)) {
          hasFavorite = true;
        }
      });

      tickerMatches.push(
        <TickerMatch
          key={match.key}
          match={match}
          hasFavorite={hasFavorite}
          isBlueZone={props.isBlueZone}
        />
      );
    }
  });

  let swapButton;
  if (NUM_VIEWS_FOR_LAYOUT[props.layoutId] === 1) {
    swapButton = null;
  } else {
    swapButton = (
      <IconButton
        tooltip="Swap position"
        tooltipPosition="top-center"
        onClick={() => props.onRequestSwapPosition()}
        touch
      >
        <SwapIcon color={white} />
      </IconButton>
    );
  }

  return (
    <Toolbar style={toolbarStyle}>
      <ToolbarGroup>
        <FlatButton
          label={props.webcast.name}
          style={titleStyle}
          href={`/event/${props.webcast.key}`}
          target="_blank"
          rel="noopener noreferrer"
          disabled={props.specialWebcastIds.has(props.webcast.id)}
        />
      </ToolbarGroup>
      <ToolbarGroup style={matchTickerGroupStyle}>
        <div style={matchTickerStyle}>{tickerMatches}</div>
      </ToolbarGroup>
      <ToolbarGroup lastChild style={controlsStyle}>
        {swapButton}
        <IconButton
          tooltip="Change webcast"
          tooltipPosition="top-center"
          onClick={() => props.onRequestSelectWebcast()}
          touch
        >
          <VideocamIcon color={white} />
        </IconButton>
        <IconButton
          tooltip={
            props.livescoreOn
              ? "Switch to webcast view"
              : "Switch to live scores view"
          }
          tooltipPosition="top-center"
          onClick={() => props.onRequestLiveScoresToggle()}
          touch
        >
          <EqualizerIcon color={props.livescoreOn ? green500 : white} />
        </IconButton>
        <IconButton
          onClick={() => props.removeWebcast(props.webcast.id)}
          tooltip="Close webcast"
          tooltipPosition="top-left"
          touch
        >
          <CloseIcon color={white} />
        </IconButton>
      </ToolbarGroup>
    </Toolbar>
  );
};

VideoCellToolbar.propTypes = {
  matches: PropTypes.arrayOf(PropTypes.object).isRequired,
  webcast: PropTypes.object.isRequired,
  specialWebcastIds: PropTypes.instanceOf(Set).isRequired,
  /* eslint-disable react/no-unused-prop-types */
  isBlueZone: PropTypes.bool.isRequired,
  livescoreOn: PropTypes.bool.isRequired,
  onRequestSwapPosition: PropTypes.func.isRequired,
  onRequestSelectWebcast: PropTypes.func.isRequired,
  onRequestLiveScoresToggle: PropTypes.func.isRequired,
  /* eslint-enable react/no-unused-prop-types */
  removeWebcast: PropTypes.func.isRequired,
  style: PropTypes.object,
  layoutId: PropTypes.number.isRequired,
};

export default VideoCellToolbar;
