import React from "react";

type Props = {
  channel: string;
  visible: boolean;
};

const TwitchChatEmbed = (props: Props) => {
  const id = `twich-chat-${props.channel}`;
  const src = `https://twitch.tv/embed/${props.channel}/chat?parent=${document.location.hostname}`;
  const style = {
    display: props.visible ? null : "none",
    width: "100%",
    height: "100%",
  };

  return (
    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ display: string | null; width: string; hei... Remove this comment to see the full error message
    <div style={style}>
      <iframe
        frameBorder="0"
        scrolling="no"
        id={id}
        src={src}
        height="100%"
        width="100%"
      />
    </div>
  );
};

export default TwitchChatEmbed;
