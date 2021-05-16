"use strict";
var __importDefault =
  (this && this.__importDefault) ||
  function (mod) {
    return mod && mod.__esModule ? mod : { default: mod };
  };
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const react_1 = __importDefault(require("react"));
const classnames_1 = __importDefault(require("classnames"));
class HashtagSidebar extends react_1.default.Component {
  componentDidMount() {
    (function twitterEmbed(d, s, id) {
      const fjs = d.getElementsByTagName(s)[0];
      // @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'Location' is not assignable to p... Remove this comment to see the full error message
      const p = /^http:/.test(d.location) ? "http" : "https";
      if (!d.getElementById(id)) {
        const js = d.createElement(s);
        js.id = id;
        /* eslint-disable prefer-template */
        js.src = p + "://platform.twitter.com/widgets.js";
        /* eslint-enable prefer-template */
        // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
        fjs.parentNode.insertBefore(js, fjs);
      }
    })(document, "script", "twitter-wjs");
  }
  render() {
    const classes = classnames_1.default({
      "hashtag-sidebar": true,
    });
    const style = {
      display: this.props.enabled ? null : "none",
    };
    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ display: string | null; }' is not assignab... Remove this comment to see the full error message
    return jsx_runtime_1.jsx(
      "div",
      Object.assign(
        { className: classes, style: style },
        {
          children: jsx_runtime_1.jsx(
            "div",
            Object.assign(
              { id: "twitter-widget" },
              {
                children: jsx_runtime_1.jsx(
                  "a",
                  Object.assign(
                    {
                      className: "twitter-timeline",
                      href: "https://twitter.com/search?q=%23omgrobots",
                      "data-widget-id": "406597120632709121",
                    },
                    { children: "Tweets about #omgrobots" }
                  ),
                  void 0
                ),
              }
            ),
            void 0
          ),
        }
      ),
      void 0
    );
  }
}
exports.default = HashtagSidebar;
