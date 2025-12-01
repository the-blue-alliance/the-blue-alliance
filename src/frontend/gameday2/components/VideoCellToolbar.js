import React from "react";
import PropTypes from "prop-types";
import Toolbar from "@mui/material/Toolbar";
import IconButton from "@mui/material/IconButton";
import Button from "@mui/material/Button";
import CloseIcon from "@mui/icons-material/Close";
import CompareArrowsIcon from "@mui/icons-material/CompareArrows";
import VideocamIcon from "@mui/icons-material/Videocam";
import EqualizerIcon from "@mui/icons-material/Equalizer";
import { green, grey } from "@mui/material/colors";

import TickerMatch from "./TickerMatch";
import { NUM_VIEWS_FOR_LAYOUT } from "../constants/LayoutConstants";

const VideoCellToolbar = (props) => {
  const toolbarStyle = {
    backgroundColor: grey[900],
    ...props.style,
  };

  const white = "#fff";
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
    backgroundColor: grey[900],
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
        onClick={() => props.onRequestSwapPosition()}
        aria-label="swap"
      >
        <CompareArrowsIcon style={{ color: white }} />
      </IconButton>
    );
  }

  return (
    <Toolbar style={toolbarStyle}>
      <div>
        <Button
          style={titleStyle}
          href={`/event/${props.webcast.key}`}
          target="_blank"
          rel="noopener noreferrer"
          disabled={props.specialWebcastIds.has(props.webcast.id)}
        >
          {props.webcast.name}
        </Button>
      </div>
      <div style={matchTickerGroupStyle}>
        <div style={matchTickerStyle}>{tickerMatches}</div>
      </div>
      <div style={controlsStyle}>
        {swapButton}
        <IconButton
          onClick={() => props.onRequestSelectWebcast()}
          aria-label="change-webcast"
        >
          <VideocamIcon style={{ color: white }} />
        </IconButton>
        <IconButton
          onClick={() => props.onRequestLiveScoresToggle()}
          aria-label="toggle-livescore"
        >
          <EqualizerIcon
            style={{ color: props.livescoreOn ? green[500] : white }}
          />
        </IconButton>
        <IconButton
          onClick={() => props.removeWebcast(props.webcast.id)}
          aria-label="close-webcast"
        >
          <CloseIcon style={{ color: white }} />
        </IconButton>
      </div>
    </Toolbar>
  );
};

VideoCellToolbar.propTypes = {
  matches: PropTypes.arrayOf(PropTypes.object).isRequired,
  webcast: PropTypes.object.isRequired,
  specialWebcastIds: PropTypes.instanceOf(Set).isRequired,

  isBlueZone: PropTypes.bool.isRequired,
  livescoreOn: PropTypes.bool.isRequired,
  onRequestSwapPosition: PropTypes.func.isRequired,
  onRequestSelectWebcast: PropTypes.func.isRequired,
  onRequestLiveScoresToggle: PropTypes.func.isRequired,

  removeWebcast: PropTypes.func.isRequired,
  style: PropTypes.object,
  layoutId: PropTypes.number.isRequired,
};

export default VideoCellToolbar;
