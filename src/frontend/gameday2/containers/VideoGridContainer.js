"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_redux_1 = require("react-redux");
const VideoGrid_1 = __importDefault(require("../components/VideoGrid"));
const mapStateToProps = (state) => ({
  domOrder: state.videoGrid.domOrder,
  positionMap: state.videoGrid.positionMap,
  domOrderLivescoreOn: state.videoGrid.domOrderLivescoreOn,
  webcastsById: state.webcastsById,
  layoutId: state.videoGrid.layoutId,
});
exports.default = react_redux_1.connect(mapStateToProps)(VideoGrid_1.default);
