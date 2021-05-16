"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const EmbedUstream = (props) => {
  const channel = props.webcast.channel;
  const src = `https://www.ustream.tv/embed/${channel}?html5ui=1`;
  return jsx_runtime_1.jsx(
    "iframe",
    {
      width: "100%",
      height: "100%",
      src: src,
      scrolling: "no",
      allowFullScreen: true,
      frameBorder: "0",
      style: { border: "0 none transparent" },
    },
    void 0
  );
};
exports.default = EmbedUstream;
