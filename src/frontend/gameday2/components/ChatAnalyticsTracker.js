"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importDefault(require("react"));
const prop_types_1 = __importDefault(require("prop-types"));
const react_ga_1 = __importDefault(require("react-ga"));
class ChatAnalyticsTracker extends react_1.default.Component {
  constructor(props) {
    super(props);
    this.elapsedTime = 0; // In minutes
  }
  componentDidMount() {
    this.beginTracking();
  }
  componentDidUpdate(prevProps) {
    if (prevProps.currentChat !== this.props.currentChat) {
      this.elapsedTime = 0;
      clearInterval(this.interval);
      this.beginTracking();
    }
  }
  componentWillUnmount() {
    clearInterval(this.interval);
  }
  beginTracking() {
    this.sendTracking();
    this.interval = setInterval(this.sendTracking.bind(this), 60000);
  }
  sendTracking() {
    react_ga_1.default.event({
      category: "Selected Chat Time",
      action: this.props.currentChat,
      label: this.elapsedTime.toString(),
      value: this.elapsedTime === 0 ? 0 : 1,
    });
    this.elapsedTime += 1;
  }
  render() {
    return null;
  }
}
exports.default = ChatAnalyticsTracker;
ChatAnalyticsTracker.propTypes = {
  currentChat: prop_types_1.default.string.isRequired,
};
