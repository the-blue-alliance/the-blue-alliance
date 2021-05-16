"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
/* global videojs */
const react_1 = __importDefault(require("react"));
class EmbedHtml5 extends react_1.default.Component {
  componentDidMount() {
    // @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'videojs'.
    videojs(this.props.webcast.id, {
      width: "100%",
      height: "100%",
      autoplay: true,
      crossorigin: "anonymous",
    });
  }
  render() {
    return jsx_runtime_1.jsx(
      "video",
      Object.assign(
        {
          controls: true,
          id: this.props.webcast.id,
          className: "video-js vjs-default-skin",
        },
        {
          children: jsx_runtime_1.jsx(
            "source",
            { src: this.props.webcast.channel, type: "application/x-mpegurl" },
            void 0
          ),
        }
      ),
      void 0
    );
  }
}
exports.default = EmbedHtml5;
