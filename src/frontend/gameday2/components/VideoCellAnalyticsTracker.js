"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const react_1 = __importDefault(require("react"));
const react_ga_1 = __importDefault(require("react-ga"));
const webcastUtils_1 = require("../utils/webcastUtils");
class VideoCellAnalyticsTracker extends react_1.default.Component {
  constructor(props) {
    super(props);
    this.elapsedTime = 0; // In minutes
  }
  componentDidMount() {
    this.sendTracking();
    this.interval = setInterval(this.sendTracking.bind(this), 60000);
  }
  componentWillUnmount() {
    clearInterval(this.interval);
  }
  sendTracking() {
    const { id, type, channel, file } = this.props.webcast;
    let action = `${id}::${type}::${channel}`;
    if (file) {
      action += `::${file}`;
    }
    react_ga_1.default.event({
      category: "Webcast View Time",
      action: action.toLowerCase(),
      label: this.elapsedTime.toString(),
      value: this.elapsedTime === 0 ? 0 : 1,
    });
    this.elapsedTime += 1;
  }
  render() {
    return null;
  }
}
exports.default = VideoCellAnalyticsTracker;
VideoCellAnalyticsTracker.propTypes = {
  webcast: webcastUtils_1.webcastPropType,
};
