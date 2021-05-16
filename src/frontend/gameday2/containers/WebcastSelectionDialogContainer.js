"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_redux_1 = require("react-redux");
const WebcastSelectionDialog_1 = __importDefault(
  require("../components/WebcastSelectionDialog")
);
const selectors_1 = require("../selectors");
const mapStateToProps = (state) => ({
  webcasts: selectors_1.getWebcastIdsInDisplayOrder(state),
  webcastsById: state.webcastsById,
  specialWebcastIds: state.specialWebcastIds,
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
});
exports.default = react_redux_1.connect(mapStateToProps)(
  WebcastSelectionDialog_1.default
);
