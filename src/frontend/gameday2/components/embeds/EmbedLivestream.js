"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const EmbedLivestream = (props) => {
  const channel = props.webcast.channel;
  const file = props.webcast.file;
  const iframeSrc = `https://new.livestream.com/accounts/${channel}/events/${file}/player?width=640&height=360&autoPlay=true&mute=false`;
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
exports.default = EmbedLivestream;
