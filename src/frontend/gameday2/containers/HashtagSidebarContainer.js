"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_redux_1 = require("react-redux");
const HashtagSidebar_1 = __importDefault(
  require("../components/HashtagSidebar")
);
const mapStateToProps = (state) => ({
  enabled: state.visibility.hashtagSidebar,
});
exports.default = react_redux_1.connect(
  mapStateToProps,
  null
)(HashtagSidebar_1.default);
