"use strict";
var __rest =
  (this && this.__rest) ||
  function (s, e) {
    var t = {};
    for (var p in s)
      if (Object.prototype.hasOwnProperty.call(s, p) && e.indexOf(p) < 0)
        t[p] = s[p];
    if (s != null && typeof Object.getOwnPropertySymbols === "function")
      for (var i = 0, p = Object.getOwnPropertySymbols(s); i < p.length; i++) {
        if (
          e.indexOf(p[i]) < 0 &&
          Object.prototype.propertyIsEnumerable.call(s, p[i])
        )
          t[p[i]] = s[p[i]];
      }
    return t;
  };
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
class AnimatableContainer extends react_1.default.Component {
  constructor(props) {
    super(props);
    this.state = {
      style: props.beginStyle,
    };
  }
  componentWillUnmount() {
    clearTimeout(this.enterTimeout);
    clearTimeout(this.leaveTimeout);
  }
  componentWillEnter(callback) {
    this.componentWillAppear(callback);
  }
  componentWillAppear(callback) {
    // Timeout needed so that the component can render with the original styles
    // before we apply the ones to transition to
    setTimeout(
      () =>
        this.setState({
          style: this.props.endStyle,
        }),
      0
    );
    this.enterTimeout = setTimeout(callback, 300);
  }
  componentWillLeave(callback) {
    this.setState({
      style: this.props.beginStyle,
    });
    this.leaveTimeout = setTimeout(callback, 300);
  }
  render() {
    /* eslint-disable no-unused-vars */
    // beginStyle and endStyle are unused, but we exclude them from ...other so
    // they don't get passed as props to our div
    const _a = this.props,
      { style, children, beginStyle, endStyle } = _a,
      other = __rest(_a, ["style", "children", "beginStyle", "endStyle"]);
    return jsx_runtime_1.jsx(
      "div",
      Object.assign(
        {},
        other,
        { style: Object.assign({}, style, this.state.style) },
        { children: children }
      ),
      void 0
    );
  }
}
exports.default = AnimatableContainer;
