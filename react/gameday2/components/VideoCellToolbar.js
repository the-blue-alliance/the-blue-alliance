import React, { PropTypes } from 'react'
import { Toolbar, ToolbarGroup, ToolbarTitle } from 'material-ui/Toolbar'
import IconButton from 'material-ui/IconButton'
import CloseIcon from 'material-ui/svg-icons/navigation/close'
import SwapIcon from 'material-ui/svg-icons/action/compare-arrows'
import VideocamIcon from 'material-ui/svg-icons/av/videocam'
import { white, grey900 } from 'material-ui/styles/colors'
import TickerMatch from './TickerMatch'

const VideoCellToolbar = (props) => {
  const toolbarStyle = {
    backgroundColor: grey900,
    ...props.style,
  }

  const titleStyle = {
    color: white,
    fontSize: 16,
  }

  const matchTickerGroupStyle = {
    flexGrow: 1,
    width: '0%',  // Slightly hacky. Prevents ticker from bleeding into next cell
    overflow: 'hidden',
    whiteSpace: 'nowrap',
  }

  const matchTickerStyle = {
    overflow: 'hidden',
    whiteSpace: 'nowrap',
  }

  const controlsStyle = {
    position: 'absolute',
    right: 0,
    marginRight: 0,
    backgroundColor: grey900,
    boxShadow: '-2px 0px 15px 6px rgba(0, 0, 0, 0.5)'
  }

  // Create TickerMatches
  var compLevelsPlayOrder = {
    'qm': 1,
    'ef': 2,
    'qf': 3,
    'sf': 4,
    'f': 5,
  }
  function calculateOrder(match) {
    return compLevelsPlayOrder[match.comp_level] * 1000000 + match.match_number * 1000 + match.set_number
  }

  var matches = []
  if (props.firedux.data &&
      props.firedux.data.events &&
      props.firedux.data.events[props.webcast.key] &&
      props.firedux.data.events[props.webcast.key].matches) {
    matches = Object.values(props.firedux.data.events[props.webcast.key].matches)
  }
  matches.sort(function(match1, match2) {
    return calculateOrder(match1) - calculateOrder(match2);
  });

  var lastMatch = null
  var upcomingMatches = []
  for (var i in matches) {
    var match = matches[i]

    if (match.alliances.red.score == -1 || match.alliances.blue.score == -1) {
      upcomingMatches.push(match);
    } else {
      lastMatch = match
      upcomingMatches = []  // Reset upcomingMatches if matches get skipped
    }
  }

  var tickerMatches = []
  if (lastMatch != null) {
    tickerMatches.push(
      <TickerMatch
        key={lastMatch.key}
        match={lastMatch}
      />
    )
  }
  for (var i in upcomingMatches) {
    tickerMatches.push(
      <TickerMatch
        key={upcomingMatches[i].key}
        match={upcomingMatches[i]}
      />
    )
  }

  return (
    <Toolbar style={toolbarStyle}>
      <ToolbarGroup>
        <ToolbarTitle
          text={props.webcast.name}
          style={titleStyle}
        />
      </ToolbarGroup>
      <ToolbarGroup style={matchTickerGroupStyle}>
        <div style={matchTickerStyle}>
          {tickerMatches}
        </div>
      </ToolbarGroup>
      <ToolbarGroup lastChild style={controlsStyle}>
        <IconButton
          tooltip="Swap position"
          tooltipPosition="top-center"
          onTouchTap={() => props.onRequestOpenSwapPositionDialog()}
          touch
        >
          <SwapIcon color={white} />
        </IconButton>
        <IconButton
          tooltip="Change webcast"
          tooltipPosition="top-center"
          onTouchTap={() => props.onRequestOpenWebcastSelectionDialog()}
          touch
        >
          <VideocamIcon color={white} />
        </IconButton>
        <IconButton
          onTouchTap={() => props.removeWebcast(props.webcast.id)}
          tooltip="Close webcast"
          tooltipPosition="top-left"
          touch
        >
          <CloseIcon color={white} />
        </IconButton>
      </ToolbarGroup>
    </Toolbar>
  )
}

VideoCellToolbar.propTypes = {
  webcast: PropTypes.object.isRequired,
  /* eslint-disable react/no-unused-prop-types */
  onRequestOpenSwapPositionDialog: PropTypes.func.isRequired,
  onRequestOpenWebcastSelectionDialog: PropTypes.func.isRequired,
  /* eslint-enable react/no-unused-prop-types */
  removeWebcast: PropTypes.func.isRequired,
  style: PropTypes.object,
}

export default VideoCellToolbar
