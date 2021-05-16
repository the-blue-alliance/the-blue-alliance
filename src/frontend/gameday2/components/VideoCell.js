"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const RaisedButton_1 = __importDefault(require("material-ui/RaisedButton"));
const WebcastEmbed_1 = __importDefault(require("./WebcastEmbed"));
const VideoCellAnalyticsTracker_1 = __importDefault(
  require("./VideoCellAnalyticsTracker")
);
const LivescoreDisplayContainer_1 = __importDefault(
  require("../containers/LivescoreDisplayContainer")
);
const VideoCellToolbarContainer_1 = __importDefault(
  require("../containers/VideoCellToolbarContainer")
);
const WebcastSelectionDialogContainer_1 = __importDefault(
  require("../containers/WebcastSelectionDialogContainer")
);
const SwapPositionDialogContainer_1 = __importDefault(
  require("../containers/SwapPositionDialogContainer")
);
const LayoutConstants_1 = require("../constants/LayoutConstants");
class VideoCell extends react_1.default.Component {
  constructor(props) {
    super(props);
    this.state = {
      webcastSelectionDialogOpen: false,
      swapPositionDialogOpen: false,
    };
  }
  onRequestSwapPosition() {
    const numViewsInLayout =
      LayoutConstants_1.NUM_VIEWS_FOR_LAYOUT[this.props.layoutId];
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
  onWebcastSelected(webcastId) {
    this.props.addWebcastAtPosition(webcastId, this.props.position);
    this.onRequestCloseWebcastSelectionDialog();
  }
  onRequestLiveScoresToggle() {
    this.props.togglePositionLivescore(this.props.position);
  }
  render() {
    const cellStyle = Object.assign(
      {},
      LayoutConstants_1.LAYOUT_STYLES[this.props.layoutId][this.props.position],
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
        jsx_runtime_1.jsxs(
          "div",
          Object.assign(
            { style: cellStyle },
            {
              children: [
                this.props.livescoreOn
                  ? jsx_runtime_1.jsx(
                      LivescoreDisplayContainer_1.default,
                      { webcast: this.props.webcast },
                      void 0
                    )
                  : jsx_runtime_1.jsx(
                      WebcastEmbed_1.default,
                      { webcast: this.props.webcast },
                      void 0
                    ),
                jsx_runtime_1.jsx(
                  VideoCellToolbarContainer_1.default,
                  {
                    style: toolbarStyle,
                    webcast: this.props.webcast,
                    isBlueZone: this.props.webcast.key === "bluezone",
                    livescoreOn: this.props.livescoreOn,
                    onRequestSelectWebcast: () =>
                      this.onRequestOpenWebcastSelectionDialog(),
                    onRequestSwapPosition: () => this.onRequestSwapPosition(),
                    onRequestLiveScoresToggle: () =>
                      this.onRequestLiveScoresToggle(),
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(
                  WebcastSelectionDialogContainer_1.default,
                  {
                    open: this.state.webcastSelectionDialogOpen,
                    webcast: this.props.webcast,
                    onRequestClose: () =>
                      this.onRequestCloseWebcastSelectionDialog(),
                    onWebcastSelected: (webcastId) =>
                      this.onWebcastSelected(webcastId),
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(
                  SwapPositionDialogContainer_1.default,
                  {
                    open: this.state.swapPositionDialogOpen,
                    position: this.props.position,
                    onRequestClose: () =>
                      this.onRequestCloseSwapPositionDialog(),
                  },
                  void 0
                ),
                jsx_runtime_1.jsx(
                  VideoCellAnalyticsTracker_1.default,
                  { webcast: this.props.webcast },
                  void 0
                ),
              ],
            }
          ),
          void 0
        )
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
      jsx_runtime_1.jsxs(
        "div",
        Object.assign(
          { style: cellStyle },
          {
            children: [
              jsx_runtime_1.jsx(
                "div",
                Object.assign(
                  { style: emptyContainerStyle },
                  {
                    children: jsx_runtime_1.jsx(
                      RaisedButton_1.default,
                      {
                        label: buttonLabel,
                        style: centerButtonStyle,
                        disabled: !webcastsAreAvailable,
                        onClick: () =>
                          this.onRequestOpenWebcastSelectionDialog(),
                      },
                      void 0
                    ),
                  }
                ),
                void 0
              ),
              jsx_runtime_1.jsx(
                WebcastSelectionDialogContainer_1.default,
                {
                  open: this.state.webcastSelectionDialogOpen,
                  webcast: this.props.webcast,
                  onRequestClose: () =>
                    this.onRequestCloseWebcastSelectionDialog(),
                  onWebcastSelected: (webcastId) =>
                    this.onWebcastSelected(webcastId),
                },
                void 0
              ),
            ],
          }
        ),
        void 0
      )
    );
  }
}
exports.default = VideoCell;
