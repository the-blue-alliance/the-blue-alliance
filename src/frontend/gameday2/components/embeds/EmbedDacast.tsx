import React from "react";
import { webcastPropType } from "../../utils/webcastUtils";
type Props = {
    webcast: webcastPropType;
};
const EmbedDacast = (props: Props) => {
    const channel = props.webcast.channel;
    const file = (props.webcast as any).file;
    const iframeSrc = `https://iframe.dacast.com/b/${channel}/c/${file}`;
    // @ts-expect-error ts-migrate(2322) FIXME: Type '{ src: string; width: string; height: string... Remove this comment to see the full error message
    return (<iframe src={iframeSrc} width="100%" height="100%" frameBorder="0" scrolling="no" player="vjs5" autoPlay="true" allowFullScreen webkitallowfullscreen mozallowfullscreen oallowfullscreen msallowfullscreen/>);
};
export default EmbedDacast;
