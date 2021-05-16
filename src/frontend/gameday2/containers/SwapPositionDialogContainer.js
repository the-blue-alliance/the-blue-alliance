"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_redux_1 = require("react-redux");
const SwapPositionDialog_1 = __importDefault(
  require("../components/SwapPositionDialog")
);
const actions_1 = require("../actions");
const mapStateToProps = (state) => ({
  layoutId: state.videoGrid.layoutId,
});
const mapDispatchToProps = (dispatch) => ({
  swapWebcasts: (firstPosition, secondPosition) =>
    dispatch(actions_1.swapWebcasts(firstPosition, secondPosition)),
});
exports.default = react_redux_1.connect(
  mapStateToProps,
  mapDispatchToProps
)(SwapPositionDialog_1.default);
