"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
const LayoutAnalyticsTracker_1 = __importDefault(
  require("./LayoutAnalyticsTracker")
);
const VideoCellContainer_1 = __importDefault(
  require("../containers/VideoCellContainer")
);
const layoutUtils_1 = require("../utils/layoutUtils");
class VideoGrid extends react_1.default.Component {
  renderLayout(webcastCount) {
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
          jsx_runtime_1.jsx(
            VideoCellContainer_1.default,
            { position: position, webcast: webcast, livescoreOn: livescoreOn },
            id
          )
        );
      } else {
        videoCells.push(jsx_runtime_1.jsx("div", {}, i.toString()));
      }
    }
    return jsx_runtime_1.jsxs(
      "div",
      Object.assign(
        { style: videoGridStyle },
        {
          children: [
            videoCells,
            jsx_runtime_1.jsx(
              LayoutAnalyticsTracker_1.default,
              { layoutId: this.props.layoutId },
              void 0
            ),
          ],
        }
      ),
      void 0
    );
  }
  render() {
    const selectedLayoutId = this.props.layoutId;
    const numViews = layoutUtils_1.getNumViewsForLayout(selectedLayoutId);
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 2.
    return this.renderLayout(numViews, selectedLayoutId);
  }
}
exports.default = VideoGrid;
