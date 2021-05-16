"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_redux_1 = require("react-redux");
const VideoCellToolbar_1 = __importDefault(
  require("../components/VideoCellToolbar")
);
const actions_1 = require("../actions");
const selectors_1 = require("../selectors");
// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'state' implicitly has an 'any' type.
const mapStateToProps = (state, props) => ({
  matches: selectors_1.getTickerMatches(state, props),
  favoriteTeams: state.favoriteTeams,
  webcasts: selectors_1.getWebcastIdsInDisplayOrder(state),
  webcastsById: state.webcastsById,
  specialWebcastIds: state.specialWebcastIds,
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
});
const mapDispatchToProps = (dispatch) => ({
  removeWebcast: (id) => dispatch(actions_1.removeWebcast(id)),
  addWebcastAtPosition: (webcastId, position) =>
    dispatch(actions_1.addWebcastAtPosition(webcastId, position)),
  swapWebcasts: (firstPosition, secondPosition) =>
    dispatch(actions_1.swapWebcasts(firstPosition, secondPosition)),
});
exports.default = react_redux_1.connect(
  mapStateToProps,
  mapDispatchToProps
)(VideoCellToolbar_1.default);
