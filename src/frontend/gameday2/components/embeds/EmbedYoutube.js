"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const EmbedYoutube = (props) => {
  const src = `//www.youtube.com/embed/${props.webcast.channel}?autoplay=1`;
  return jsx_runtime_1.jsx(
    "iframe",
    {
      width: "100%",
      height: "100%",
      src: src,
      frameBorder: "0",
      allowFullScreen: true,
    },
    void 0
  );
};
exports.default = EmbedYoutube;
