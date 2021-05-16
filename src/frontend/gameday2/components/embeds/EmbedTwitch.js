"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const EmbedTwitch = (props) => {
  const channel = props.webcast.channel;
  const iframeSrc = `https://player.twitch.tv/?channel=${channel}&parent=${document.location.hostname}`;
  return jsx_runtime_1.jsx(
    "iframe",
    {
      src: iframeSrc,
      frameBorder: "0",
      scrolling: "no",
      height: "100%",
      width: "100%",
      allowFullScreen: true,
    },
    void 0
  );
};
exports.default = EmbedTwitch;
