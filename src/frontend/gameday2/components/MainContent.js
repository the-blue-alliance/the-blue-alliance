"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
const muiThemeable_1 = __importDefault(
  require("material-ui/styles/muiThemeable")
);
const VideoGridContainer_1 = __importDefault(
  require("../containers/VideoGridContainer")
);
const LayoutSelectionPanel_1 = __importDefault(
  require("./LayoutSelectionPanel")
);
const NoWebcasts_1 = __importDefault(require("./NoWebcasts"));
/**
 * Acts as a high-level "controller" for the main content area. This component
 * will render the appropriate child based on the state of the app. This will
 * also apply the appropriate margins to the main content area to position it
 * correctly when the sidebars are shown or hidden.
 *
 * If no webcasts are present, this displays a message for that.
 *
 * If webcasts are present but no layout is set, this displays a layout selector.
 *
 * If webcasts are present and a layout is set, this displays the video grid.
 */
const MainContent = (props) => {
  let child = null;
  if (props.webcasts.length === 0) {
    // No webcasts. Do the thing!
    child = jsx_runtime_1.jsx(NoWebcasts_1.default, {}, void 0);
  } else if (!props.layoutSet) {
    // No layout set. Display the layout selector.
    child = jsx_runtime_1.jsx(
      LayoutSelectionPanel_1.default,
      { setLayout: props.setLayout },
      void 0
    );
  } else {
    // Display the video grid
    child = jsx_runtime_1.jsx(VideoGridContainer_1.default, {}, void 0);
  }
  const contentStyles = {
    position: "absolute",
    top: props.muiTheme.layout.appBarHeight,
    left: 0,
    right: 0,
    bottom: 0,
    marginRight: props.chatSidebarVisible
      ? props.muiTheme.layout.chatPanelWidth
      : 0,
    marginLeft: props.hashtagSidebarVisible
      ? props.muiTheme.layout.socialPanelWidth
      : 0,
  };
  // @ts-expect-error ts-migrate(2322) FIXME: Type '{ position: string; top: any; left: number; ... Remove this comment to see the full error message
  return jsx_runtime_1.jsx(
    "div",
    Object.assign({ style: contentStyles }, { children: child }),
    void 0
  );
};
exports.default = muiThemeable_1.default()(MainContent);
