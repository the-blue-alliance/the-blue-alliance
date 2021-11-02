import React from "react";
import { webcastPropType } from "../../utils/webcastUtils";
type Props = {
    webcast: webcastPropType;
};
const EmbedLivestream = (props: Props) => {
    const channel = props.webcast.channel;
    const file = (props.webcast as any).file;
    const iframeSrc = `https://new.livestream.com/accounts/${channel}/events/${file}/player?width=640&height=360&autoPlay=true&mute=false`;
    return (<iframe src={iframeSrc} frameBorder="0" scrolling="no" height="100%" width="100%" allowFullScreen/>);
};
export default EmbedLivestream;
