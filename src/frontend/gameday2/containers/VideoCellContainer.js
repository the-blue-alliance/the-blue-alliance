"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_redux_1 = require("react-redux");
const VideoCell_1 = __importDefault(require("../components/VideoCell"));
const actions_1 = require("../actions");
const selectors_1 = require("../selectors");
const mapStateToProps = (state) => ({
  webcasts: selectors_1.getWebcastIdsInDisplayOrder(state),
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
});
const mapDispatchToProps = (dispatch) => ({
  addWebcastAtPosition: (webcastId, position) =>
    dispatch(actions_1.addWebcastAtPosition(webcastId, position)),
  setLayout: (layoutId) => dispatch(actions_1.setLayout(layoutId)),
  swapWebcasts: (firstPosition, secondPosition) =>
    dispatch(actions_1.swapWebcasts(firstPosition, secondPosition)),
  togglePositionLivescore: (position) =>
    dispatch(actions_1.togglePositionLivescore(position)),
});
exports.default = react_redux_1.connect(
  mapStateToProps,
  mapDispatchToProps
)(VideoCell_1.default);
