"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const EmbedIframe = (props) => {
  const divStyle = {
    width: "100%",
    height: "100%",
  };
  let iframeMarkup = props.webcast.channel;
  iframeMarkup = iframeMarkup.replace(/&lt;/, "<");
  iframeMarkup = iframeMarkup.replace(/&gt;/, ">");
  const markup = {
    __html: iframeMarkup,
  };
  const elem = jsx_runtime_1.jsx(
    "div",
    { style: divStyle, dangerouslySetInnerHTML: markup },
    void 0
  );
  return elem;
};
exports.default = EmbedIframe;
