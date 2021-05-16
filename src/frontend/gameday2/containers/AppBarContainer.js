"use strict";
var __createBinding =
  (this && this.__createBinding) ||
  (Object.create
    ? function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        Object.defineProperty(o, k2, {
          enumerable: true,
          get: function () {
            return m[k];
          },
        });
      }
    : function (o, m, k, k2) {
        if (k2 === undefined) k2 = k;
        o[k2] = m[k];
      });
var __setModuleDefault =
  (this && this.__setModuleDefault) ||
  (Object.create
    ? function (o, v) {
        Object.defineProperty(o, "default", { enumerable: true, value: v });
      }
    : function (o, v) {
        o["default"] = v;
      });
var __importStar =
  (this && this.__importStar) ||
  function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null)
      for (var k in mod)
        if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k))
          __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
  };
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_redux_1 = require("react-redux");
const AppBar_1 = __importDefault(require("../components/AppBar"));
const actions = __importStar(require("../actions"));
const selectors_1 = require("../selectors");
const mapStateToProps = (state) => ({
  webcasts: selectors_1.getWebcastIdsInDisplayOrder(state),
  layoutId: state.videoGrid.layoutId,
  layoutSet: state.videoGrid.layoutSet,
  hashtagSidebarVisible: state.visibility.hashtagSidebar,
  chatSidebarVisible: state.visibility.chatSidebar,
  layoutDrawerVisible: state.visibility.layoutDrawer,
});
const mapDispatchToProps = (dispatch) => ({
  toggleChatSidebarVisibility: () =>
    dispatch(actions.toggleChatSidebarVisibility()),
  setChatSidebarVisibility: (visible) =>
    dispatch(actions.setChatSidebarVisibility(visible)),
  toggleHashtagSidebarVisibility: () =>
    dispatch(actions.toggleHashtagSidebarVisibility()),
  setHashtagSidebarVisibility: (visible) =>
    dispatch(actions.setHashtagSidebarVisibility(visible)),
  resetWebcasts: () => dispatch(actions.resetWebcasts()),
  setLayout: (layoutId) => dispatch(actions.setLayout(layoutId)),
  toggleLayoutDrawerVisibility: () =>
    dispatch(actions.toggleLayoutDrawerVisibility()),
  setLayoutDrawerVisibility: (visible) =>
    dispatch(actions.setLayoutDrawerVisibility(visible)),
});
exports.default = react_redux_1.connect(
  mapStateToProps,
  mapDispatchToProps
)(AppBar_1.default);
