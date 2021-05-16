"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
const react_countup_1 = __importDefault(require("react-countup"));
class CountWrapper extends react_1.default.PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      start: props.number,
      end: props.number,
    };
  }
  UNSAFE_componentWillUpdate(nextProps) {
    this.setState({
      start: this.state.end,
      end: nextProps.number,
    });
  }
  render() {
    return jsx_runtime_1.jsx(
      react_countup_1.default,
      { start: this.state.start, end: this.state.end, duration: 1 },
      void 0
    );
  }
}
exports.default = CountWrapper;
