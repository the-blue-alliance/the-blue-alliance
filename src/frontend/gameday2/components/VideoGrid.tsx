import React from "react";
import LayoutAnalyticsTracker from "./LayoutAnalyticsTracker";
import VideoCellContainer from "../containers/VideoCellContainer";
import { getNumViewsForLayout } from "../utils/layoutUtils";
import { webcastPropType } from "../utils/webcastUtils";

type Props = {
  domOrder: string[];
  positionMap: number[];
  domOrderLivescoreOn: boolean[];
  webcastsById: {
    [key: string]: webcastPropType;
  };
  layoutId: number;
};

export default class VideoGrid extends React.Component<Props> {
  renderLayout(webcastCount: any) {
    const videoGridStyle = {
      width: "100%",
      height: "100%",
    };

    const { domOrder, positionMap, domOrderLivescoreOn } = this.props;

    // Set up reverse map between webcast ID and position
    const idPositionMap = {};
    for (let i = 0; i < positionMap.length; i++) {
      const webcastId = domOrder[positionMap[i]];
      if (webcastId != null) {
        // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
        idPositionMap[webcastId] = i;
      }
    }

    // Compute which cells don't a webcast in them
    const emptyCellPositions = [];
    for (let i = 0; i < positionMap.length; i++) {
      if (positionMap[i] === -1 && i < webcastCount) {
        emptyCellPositions.push(i);
      }
    }

    // Render everything!
    const videoCells = [];
    for (let i = 0; i < domOrder.length; i++) {
      let webcast = null;
      let id = `video-${i}`;
      let position = null;
      let hasWebcast = true;
      let livescoreOn = false;
      if (domOrder[i]) {
        // There's a webcast to display here!
        webcast = this.props.webcastsById[domOrder[i]];
        id = webcast.id;
        // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
        position = idPositionMap[id];
        livescoreOn = domOrderLivescoreOn[i];
      } else if (emptyCellPositions.length > 0) {
        position = emptyCellPositions.shift();
      } else {
        hasWebcast = false;
      }
      if (hasWebcast) {
        videoCells.push(
          <VideoCellContainer
            position={position}
            key={id}
            webcast={webcast}
            livescoreOn={livescoreOn}
          />
        );
      } else {
        videoCells.push(<div key={i.toString()} />);
      }
    }

    return (
      <div style={videoGridStyle}>
        {videoCells}
        <LayoutAnalyticsTracker layoutId={this.props.layoutId} />
      </div>
    );
  }

  render() {
    const selectedLayoutId = this.props.layoutId;
    const numViews = getNumViewsForLayout(selectedLayoutId);
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 2.
    return this.renderLayout(numViews, selectedLayoutId);
  }
}
