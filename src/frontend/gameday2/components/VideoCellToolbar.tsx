import React from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import { Toolbar, ToolbarGroup } from "material-ui/Toolbar";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import FlatButton from "material-ui/FlatButton";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import IconButton from "material-ui/IconButton";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import CloseIcon from "material-ui/svg-icons/navigation/close";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import SwapIcon from "material-ui/svg-icons/action/compare-arrows";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import VideocamIcon from "material-ui/svg-icons/av/videocam";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import EqualizerIcon from "material-ui/svg-icons/av/equalizer";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import { white, green500, grey900 } from "material-ui/styles/colors";
import TickerMatch from "./TickerMatch";
import { NUM_VIEWS_FOR_LAYOUT } from "../constants/LayoutConstants";
type Props = {
    matches: any[];
    webcast: any;
    specialWebcastIds: any; // TODO: PropTypes.instanceOf(Set)
    isBlueZone: boolean;
    livescoreOn: boolean;
    onRequestSwapPosition: (...args: any[]) => any;
    onRequestSelectWebcast: (...args: any[]) => any;
    onRequestLiveScoresToggle: (...args: any[]) => any;
    removeWebcast: (...args: any[]) => any;
    style?: any;
    layoutId: number;
};
const VideoCellToolbar = (props: Props) => {
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
        width: "0%",
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
    const tickerMatches: any = [];
    props.matches.forEach((match) => {
        // See if match has a favorite team
        let hasFavorite = false;
        const teamKeys = match.rt.concat(match.bt);
        teamKeys.forEach((teamKey: any) => {
            if ((props as any).favoriteTeams.has(teamKey)) {
                hasFavorite = true;
            }
        });
        tickerMatches.push(<TickerMatch key={match.key} match={match} hasFavorite={hasFavorite} isBlueZone={props.isBlueZone}/>);
    });
    let swapButton;
    if (NUM_VIEWS_FOR_LAYOUT[props.layoutId] === 1) {
        swapButton = null;
    }
    else {
        swapButton = (<IconButton tooltip="Swap position" tooltipPosition="top-center" onClick={() => props.onRequestSwapPosition()} touch>
        <SwapIcon color={white}/>
      </IconButton>);
    }
    return (<Toolbar style={toolbarStyle}>
      <ToolbarGroup>
        <FlatButton label={props.webcast.name} style={titleStyle} href={`/event/${props.webcast.key}`} target="_blank" disabled={props.specialWebcastIds.has(props.webcast.id)}/>
      </ToolbarGroup>
      <ToolbarGroup style={matchTickerGroupStyle}>
        {/* @ts-expect-error ts-migrate(2322) FIXME: Type '{ overflow: string; whiteSpace: string; }' i... Remove this comment to see the full error message */}
        <div style={matchTickerStyle}>{tickerMatches}</div>
      </ToolbarGroup>
      <ToolbarGroup lastChild style={controlsStyle}>
        {swapButton}
        <IconButton tooltip="Change webcast" tooltipPosition="top-center" onClick={() => props.onRequestSelectWebcast()} touch>
          <VideocamIcon color={white}/>
        </IconButton>
        <IconButton tooltip={props.livescoreOn
            ? "Switch to webcast view"
            : "Switch to live scores view"} tooltipPosition="top-center" onClick={() => props.onRequestLiveScoresToggle()} touch>
          <EqualizerIcon color={props.livescoreOn ? green500 : white}/>
        </IconButton>
        <IconButton onClick={() => props.removeWebcast(props.webcast.id)} tooltip="Close webcast" tooltipPosition="top-left" touch>
          <CloseIcon color={white}/>
        </IconButton>
      </ToolbarGroup>
    </Toolbar>);
};
export default VideoCellToolbar;
