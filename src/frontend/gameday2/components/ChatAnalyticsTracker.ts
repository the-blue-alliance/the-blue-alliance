import React from "react";
import PropTypes from "prop-types";
import ReactGA from "react-ga";
export default class ChatAnalyticsTracker extends React.Component {
    static propTypes = {
        currentChat: PropTypes.string.isRequired,
    };
    elapsedTime: any;
    interval: any;
    constructor(props: any) {
        super(props);
        this.elapsedTime = 0; // In minutes
    }
    componentDidMount() {
        this.beginTracking();
    }
    componentDidUpdate(prevProps: any) {
        if (prevProps.currentChat !== (this.props as any).currentChat) {
            this.elapsedTime = 0;
            clearInterval(this.interval);
            this.beginTracking();
        }
    }
    componentWillUnmount() {
        clearInterval(this.interval);
    }
    beginTracking() {
        this.sendTracking();
        this.interval = setInterval(this.sendTracking.bind(this), 60000);
    }
    sendTracking() {
        ReactGA.event({
            category: "Selected Chat Time",
            action: (this.props as any).currentChat,
            label: this.elapsedTime.toString(),
            value: this.elapsedTime === 0 ? 0 : 1,
        });
        this.elapsedTime += 1;
    }
    render() {
        return null;
    }
}
