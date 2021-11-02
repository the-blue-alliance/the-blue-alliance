import React from "react";
import classNames from "classnames";
type Props = {
    enabled?: boolean;
};
export default class HashtagSidebar extends React.Component<Props> {
    componentDidMount() {
        (function twitterEmbed(d, s, id) {
            const fjs = d.getElementsByTagName(s)[0];
            // @ts-expect-error ts-migrate(2345) FIXME: Argument of type 'Location' is not assignable to p... Remove this comment to see the full error message
            const p = /^http:/.test(d.location) ? "http" : "https";
            if (!d.getElementById(id)) {
                const js = d.createElement(s);
                js.id = id;
                /* eslint-disable prefer-template */
                (js as any).src = p + "://platform.twitter.com/widgets.js";
                /* eslint-enable prefer-template */
                // @ts-expect-error ts-migrate(2531) FIXME: Object is possibly 'null'.
                fjs.parentNode.insertBefore(js, fjs);
            }
        })(document, "script", "twitter-wjs");
    }
    render() {
        const classes = classNames({
            "hashtag-sidebar": true,
        });
        const style = {
            display: this.props.enabled ? null : "none",
        };
        // @ts-expect-error ts-migrate(2322) FIXME: Type '{ display: string | null; }' is not assignab... Remove this comment to see the full error message
        return (<div className={classes} style={style}>
        <div id="twitter-widget">
          <a className="twitter-timeline" href="https://twitter.com/search?q=%23omgrobots" data-widget-id="406597120632709121">
            Tweets about #omgrobots
          </a>
        </div>
      </div>);
    }
}
