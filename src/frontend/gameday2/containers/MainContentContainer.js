"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_redux_1 = require("react-redux");
const MainContent_1 = __importDefault(require("../components/MainContent"));
const actions_1 = require("../actions");
const selectors_1 = require("../selectors");
const mapStateToProps = (state) => ({
  webcasts: selectors_1.getWebcastIds(state),
  hashtagSidebarVisible: state.visibility.hashtagSidebar,
  chatSidebarVisible: state.visibility.chatSidebar,
  layoutSet: state.videoGrid.layoutSet,
});
const mapDispatchToProps = (dispatch) => ({
  setLayout: (layoutId) => dispatch(actions_1.setLayout(layoutId)),
});
exports.default = react_redux_1.connect(
  mapStateToProps,
  mapDispatchToProps
)(MainContent_1.default);
