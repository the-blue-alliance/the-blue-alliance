import React from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import RaisedButton from "material-ui/RaisedButton";
import WebcastEmbed from "./WebcastEmbed";
import VideoCellAnalyticsTracker from "./VideoCellAnalyticsTracker";
import LivescoreDisplayContainer from "../containers/LivescoreDisplayContainer";
import VideoCellToolbarContainer from "../containers/VideoCellToolbarContainer";
import WebcastSelectionDialogContainer from "../containers/WebcastSelectionDialogContainer";
import SwapPositionDialogContainer from "../containers/SwapPositionDialogContainer";
import { webcastPropType } from "../utils/webcastUtils";
import {
  LAYOUT_STYLES,
  NUM_VIEWS_FOR_LAYOUT,
} from "../constants/LayoutConstants";

type Props = {
  webcast?: webcastPropType;
  webcasts: string[];
  displayedWebcasts: string[];
  layoutId: number;
  position: number;
  livescoreOn: boolean;
  addWebcastAtPosition: (...args: any[]) => any;
  swapWebcasts: (...args: any[]) => any;
  togglePositionLivescore: (...args: any[]) => any;
};

type State = any;

export default class VideoCell extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      webcastSelectionDialogOpen: false,
      swapPositionDialogOpen: false,
    };
  }

  onRequestSwapPosition() {
    const numViewsInLayout = NUM_VIEWS_FOR_LAYOUT[this.props.layoutId];
    if (numViewsInLayout === 2) {
      // It doesn't matter which position we are
      this.props.swapWebcasts(0, 1);
    } else {
      this.onRequestOpenSwapPositionDialog();
    }
  }

  onRequestOpenWebcastSelectionDialog() {
    this.setState({ webcastSelectionDialogOpen: true });
  }

  onRequestCloseWebcastSelectionDialog() {
    this.setState({ webcastSelectionDialogOpen: false });
  }

  onRequestOpenSwapPositionDialog() {
    this.setState({ swapPositionDialogOpen: true });
  }

  onRequestCloseSwapPositionDialog() {
    this.setState({ swapPositionDialogOpen: false });
  }

  onWebcastSelected(webcastId: any) {
    this.props.addWebcastAtPosition(webcastId, this.props.position);
    this.onRequestCloseWebcastSelectionDialog();
  }

  onRequestLiveScoresToggle() {
    this.props.togglePositionLivescore(this.props.position);
  }

  render() {
    const cellStyle = Object.assign(
      {},
      LAYOUT_STYLES[this.props.layoutId][this.props.position],
      {
        paddingBottom: "48px",
        outline: "#fff solid 1px",
      }
    );

    if (this.props.webcast) {
      const toolbarStyle = {
        position: "absolute",
        bottom: 0,
        width: "100%",
        height: "48px",
        paddingLeft: "8px",
      };

      return (
        // @ts-expect-error ts-migrate(2322) FIXME: Type '({ width: string; height: string; top: numbe... Remove this comment to see the full error message
        <div style={cellStyle}>
          {this.props.livescoreOn ? (
            <LivescoreDisplayContainer webcast={this.props.webcast} />
          ) : (
            <WebcastEmbed webcast={this.props.webcast} />
          )}
          <VideoCellToolbarContainer
            style={toolbarStyle}
            webcast={this.props.webcast}
            isBlueZone={this.props.webcast.key === "bluezone"}
            livescoreOn={this.props.livescoreOn}
            onRequestSelectWebcast={() =>
              this.onRequestOpenWebcastSelectionDialog()
            }
            onRequestSwapPosition={() => this.onRequestSwapPosition()}
            onRequestLiveScoresToggle={() => this.onRequestLiveScoresToggle()}
          />
          <WebcastSelectionDialogContainer
            open={this.state.webcastSelectionDialogOpen}
            webcast={this.props.webcast}
            onRequestClose={() => this.onRequestCloseWebcastSelectionDialog()}
            onWebcastSelected={(webcastId: any) =>
              this.onWebcastSelected(webcastId)
            }
          />
          <SwapPositionDialogContainer
            open={this.state.swapPositionDialogOpen}
            position={this.props.position}
            onRequestClose={() => this.onRequestCloseSwapPositionDialog()}
          />
          <VideoCellAnalyticsTracker webcast={this.props.webcast} />
        </div>
      );
    }

    const emptyContainerStyle = {
      width: "100%",
      height: "100%",
    };

    const centerButtonStyle = {
      position: "absolute",
      top: "50%",
      left: "50%",
      transform: "translateX(-50%) translateY(-50%)",
    };

    // All positions in this array which are non-null represent displayed webcasts
    const displayedCount = this.props.displayedWebcasts.reduce(
      (acc, curr) => acc + (curr == null ? 0 : 1),
      0
    );

    const webcastsAreAvailable = this.props.webcasts.length !== displayedCount;
    const buttonLabel = webcastsAreAvailable
      ? "Select a webcast"
      : "No more webcasts available";

    return (
      // @ts-expect-error ts-migrate(2322) FIXME: Type '({ width: string; height: string; top: numbe... Remove this comment to see the full error message
      <div style={cellStyle}>
        <div style={emptyContainerStyle}>
          <RaisedButton
            label={buttonLabel}
            style={centerButtonStyle}
            disabled={!webcastsAreAvailable}
            onClick={() => this.onRequestOpenWebcastSelectionDialog()}
          />
        </div>
        <WebcastSelectionDialogContainer
          open={this.state.webcastSelectionDialogOpen}
          webcast={this.props.webcast}
          onRequestClose={() => this.onRequestCloseWebcastSelectionDialog()}
          onWebcastSelected={(webcastId: any) =>
            this.onWebcastSelected(webcastId)
          }
        />
      </div>
    );
  }
}
