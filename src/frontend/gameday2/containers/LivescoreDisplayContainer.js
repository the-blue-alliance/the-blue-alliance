"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_redux_1 = require("react-redux");
const LivescoreDisplay_1 = __importDefault(
  require("../components/LivescoreDisplay")
);
const selectors_1 = require("../selectors");
// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'state' implicitly has an 'any' type.
const mapStateToProps = (state, props) => ({
  matches: selectors_1.getEventMatches(state, props),
  matchState: selectors_1.getCurrentMatchState(state, props),
});
exports.default = react_redux_1.connect(mapStateToProps)(
  LivescoreDisplay_1.default
);
