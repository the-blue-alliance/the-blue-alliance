import React from "react";
import PropTypes from "prop-types";
import ReactGA from "react-ga";
import { NAME_FOR_LAYOUT } from "../constants/LayoutConstants";
export default class LayoutAnalyticsTracker extends React.Component {
    static propTypes = {
        layoutId: PropTypes.number.isRequired,
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
        if (prevProps.layoutId !== (this.props as any).layoutId) {
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
            category: "Selected Layout Time",
            action: NAME_FOR_LAYOUT[(this.props as any).layoutId],
            label: this.elapsedTime.toString(),
            value: this.elapsedTime === 0 ? 0 : 1,
        });
        this.elapsedTime += 1;
    }
    render() {
        return null;
    }
}
