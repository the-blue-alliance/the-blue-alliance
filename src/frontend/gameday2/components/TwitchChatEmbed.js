"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const jsx_runtime_1 = require("react/jsx-runtime");
const TwitchChatEmbed = (props) => {
  const id = `twich-chat-${props.channel}`;
  const src = `https://twitch.tv/embed/${props.channel}/chat?parent=${document.location.hostname}`;
  const style = {
    display: props.visible ? null : "none",
    width: "100%",
    height: "100%",
  };
  return (
    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ display: string | null; width: string; hei... Remove this comment to see the full error message
    jsx_runtime_1.jsx(
      "div",
      Object.assign(
        { style: style },
        {
          children: jsx_runtime_1.jsx(
            "iframe",
            {
              frameBorder: "0",
              scrolling: "no",
              id: id,
              src: src,
              height: "100%",
              width: "100%",
            },
            void 0
          ),
        }
      ),
      void 0
    )
  );
};
exports.default = TwitchChatEmbed;
