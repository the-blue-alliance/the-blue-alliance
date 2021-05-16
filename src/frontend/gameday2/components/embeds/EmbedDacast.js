"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const EmbedDacast = (props) => {
  const channel = props.webcast.channel;
  const file = props.webcast.file;
  const iframeSrc = `https://iframe.dacast.com/b/${channel}/c/${file}`;
  // @ts-expect-error ts-migrate(2322) FIXME: Type '{ src: string; width: string; height: string... Remove this comment to see the full error message
  return jsx_runtime_1.jsx(
    "iframe",
    {
      src: iframeSrc,
      width: "100%",
      height: "100%",
      frameBorder: "0",
      scrolling: "no",
      player: "vjs5",
      autoPlay: "true",
      allowFullScreen: true,
      webkitallowfullscreen: true,
      mozallowfullscreen: true,
      oallowfullscreen: true,
      msallowfullscreen: true,
    },
    void 0
  );
};
exports.default = EmbedDacast;
