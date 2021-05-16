"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
const EmbedUstream_1 = __importDefault(require("./embeds/EmbedUstream"));
const EmbedYoutube_1 = __importDefault(require("./embeds/EmbedYoutube"));
const EmbedTwitch_1 = __importDefault(require("./embeds/EmbedTwitch"));
const EmbedLivestream_1 = __importDefault(require("./embeds/EmbedLivestream"));
const EmbedIframe_1 = __importDefault(require("./embeds/EmbedIframe"));
const EmbedHtml5_1 = __importDefault(require("./embeds/EmbedHtml5"));
const EmbedDacast_1 = __importDefault(require("./embeds/EmbedDacast"));
const EmbedDirectLink_1 = __importDefault(require("./embeds/EmbedDirectLink"));
const EmbedRtmp_1 = __importDefault(require("./embeds/EmbedRtmp"));
const EmbedNotSupported_1 = __importDefault(
  require("./embeds/EmbedNotSupported")
);
class WebcastEmbed extends react_1.default.Component {
  render() {
    let cellEmbed;
    // @ts-expect-error ts-migrate(2532) FIXME: Object is possibly 'undefined'.
    switch (this.props.webcast.type) {
      case "ustream":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = jsx_runtime_1.jsx(
          EmbedUstream_1.default,
          { webcast: this.props.webcast },
          void 0
        );
        break;
      case "youtube":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = jsx_runtime_1.jsx(
          EmbedYoutube_1.default,
          { webcast: this.props.webcast },
          void 0
        );
        break;
      case "twitch":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = jsx_runtime_1.jsx(
          EmbedTwitch_1.default,
          { webcast: this.props.webcast },
          void 0
        );
        break;
      case "livestream":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = jsx_runtime_1.jsx(
          EmbedLivestream_1.default,
          { webcast: this.props.webcast },
          void 0
        );
        break;
      case "iframe":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = jsx_runtime_1.jsx(
          EmbedIframe_1.default,
          { webcast: this.props.webcast },
          void 0
        );
        break;
      case "html5":
        // @ts-expect-error ts-migrate(2769) FIXME: No overload matches this call.
        cellEmbed = jsx_runtime_1.jsx(
          EmbedHtml5_1.default,
          { webcast: this.props.webcast },
          void 0
        );
        break;
      case "dacast":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = jsx_runtime_1.jsx(
          EmbedDacast_1.default,
          { webcast: this.props.webcast },
          void 0
        );
        break;
      case "direct_link":
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'webcastPropType | undefined' is not assignab... Remove this comment to see the full error message
        cellEmbed = jsx_runtime_1.jsx(
          EmbedDirectLink_1.default,
          { webcast: this.props.webcast },
          void 0
        );
        break;
      case "rtmp":
        // @ts-expect-error ts-migrate(2769) FIXME: No overload matches this call.
        cellEmbed = jsx_runtime_1.jsx(
          EmbedRtmp_1.default,
          { webcast: this.props.webcast },
          void 0
        );
        break;
      default:
        cellEmbed = jsx_runtime_1.jsx(EmbedNotSupported_1.default, {}, void 0);
        break;
    }
    return cellEmbed;
  }
}
exports.default = WebcastEmbed;
