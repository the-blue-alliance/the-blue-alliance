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
const Dialog_1 = __importDefault(require("material-ui/Dialog"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const FlatButton_1 = __importDefault(require("material-ui/FlatButton"));
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'reac... Remove this comment to see the full error message
const react_event_listener_1 = __importDefault(require("react-event-listener"));
const SwapPositionPreviewCell_1 = __importDefault(
  require("./SwapPositionPreviewCell")
);
const LayoutConstants_1 = require("../constants/LayoutConstants");
class SwapPositionDialog extends react_1.default.Component {
  componentDidMount() {
    this.updateSizing();
  }
  componentDidUpdate() {
    this.updateSizing();
  }
  onRequestSwap(targetPosition) {
    this.props.swapWebcasts(this.props.position, targetPosition);
    this.onRequestClose();
  }
  onRequestClose() {
    if (this.props.onRequestClose) {
      this.props.onRequestClose();
    }
  }
  updateSizing() {
    const container = this.container;
    if (this.props.open && container) {
      const windowWidth = window.innerWidth;
      const windowHeight = window.innerHeight;
      const aspectRatio = windowWidth / windowHeight;
      const containerWidth = container.offsetWidth;
      const containerHeight = containerWidth / aspectRatio;
      container.style.height = `${containerHeight}px`;
    }
  }
  render() {
    const videoViews = [];
    const layoutId = this.props.layoutId;
    for (let i = 0; i < LayoutConstants_1.NUM_VIEWS_FOR_LAYOUT[layoutId]; i++) {
      const cellStyle = LayoutConstants_1.LAYOUT_STYLES[layoutId][i];
      videoViews.push(
        jsx_runtime_1.jsx(
          SwapPositionPreviewCell_1.default,
          {
            style: cellStyle,
            enabled: i !== this.props.position,
            onClick: () => this.onRequestSwap(i),
          },
          i.toString()
        )
      );
    }
    const actions = [
      jsx_runtime_1.jsx(
        FlatButton_1.default,
        {
          label: "Cancel",
          primary: true,
          onClick: () => this.onRequestClose(),
        },
        void 0
      ),
    ];
    const bodyStyle = {
      padding: 8,
    };
    const previewContainerStyle = {
      padding: "4px",
      position: "relative",
    };
    return jsx_runtime_1.jsxs(
      Dialog_1.default,
      Object.assign(
        {
          title: "Select a position to swap with",
          actions: actions,
          modal: false,
          bodyStyle: bodyStyle,
          open: this.props.open,
          onRequestClose: () => this.onRequestClose(),
          autoScrollBodyContent: true,
        },
        {
          children: [
            jsx_runtime_1.jsx(
              react_event_listener_1.default,
              { target: "window", onResize: () => this.updateSizing() },
              void 0
            ),
            jsx_runtime_1.jsx(
              "div",
              Object.assign(
                {
                  // @ts-expect-error ts-migrate(2322) FIXME: Type '{ padding: string; position: string; }' is n... Remove this comment to see the full error message
                  style: previewContainerStyle,
                  ref: (e) => {
                    this.container = e;
                    this.updateSizing();
                  },
                },
                { children: videoViews }
              ),
              void 0
            ),
          ],
        }
      ),
      void 0
    );
  }
}
exports.default = SwapPositionDialog;
