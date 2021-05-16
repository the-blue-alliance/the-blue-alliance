"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
function getStyles(props, state) {
  let backgroundColor;
  if (props.enabled) {
    if (state.hovered) {
      backgroundColor = "#aaaaaa";
    } else {
      backgroundColor = "#cccccc";
    }
  } else {
    backgroundColor = "#555555";
  }
  const style = {
    padding: "4px",
    backgroundClip: "content-box",
    backgroundColor,
    cursor: props.enabled ? "pointer" : null,
  };
  return Object.assign({}, style, props.style);
}
class SwapPositionPreviewCell extends react_1.default.Component {
  constructor(props) {
    super(props);
    this.state = {
      hovered: false,
    };
  }
  onMouseOver() {
    this.setState({
      hovered: true,
    });
  }
  onMouseOut() {
    this.setState({
      hovered: false,
    });
  }
  onClick() {
    if (this.props.onClick) {
      this.props.onClick();
    }
  }
  render() {
    const styles = getStyles(this.props, this.state);
    return jsx_runtime_1.jsx(
      "div",
      {
        style: styles,
        onMouseOver: () => this.onMouseOver(),
        onMouseOut: () => this.onMouseOut(),
        onClick: () => this.onClick(),
      },
      void 0
    );
  }
}
exports.default = SwapPositionPreviewCell;
