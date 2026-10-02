import React from "react";
import PropTypes from "prop-types";

export default class AnimatableContainer extends React.Component {
  static propTypes = {
    beginStyle: PropTypes.object.isRequired,
    endStyle: PropTypes.object.isRequired,
    style: PropTypes.object,
    children: PropTypes.node,
    in: PropTypes.bool,
    onExited: PropTypes.func,
  };

  constructor(props) {
    super(props);

    this.state = {
      style: props.beginStyle,
    };
  }

  // react-transition-group v4 drives children through `in` and `onExited`.
  componentDidMount() {
    if (this.props.in) {
      this.componentWillAppear(() => {});
    }
  }

  componentDidUpdate(prevProps) {
    if (!prevProps.in && this.props.in) {
      clearTimeout(this.leaveTimeout);
      this.componentWillEnter(() => {});
    } else if (prevProps.in && !this.props.in) {
      this.componentWillLeave(() => this.props.onExited?.());
    }
  }

  componentWillUnmount() {
    clearTimeout(this.enterTimeout);
    clearTimeout(this.leaveTimeout);
  }

  componentWillEnter(callback) {
    this.componentWillAppear(callback);
  }

  componentWillAppear(callback) {
    // Timeout needed so that the component can render with the original styles
    // before we apply the ones to transition to
    setTimeout(
      () =>
        this.setState({
          style: this.props.endStyle,
        }),
      0
    );

    this.enterTimeout = setTimeout(callback, 300);
  }

  componentWillLeave(callback) {
    this.setState({
      style: this.props.beginStyle,
    });

    this.leaveTimeout = setTimeout(callback, 300);
  }

  render() {
    // Exclude animation and transition-group props so they don't reach the div
    const {
      style,
      children,
      beginStyle,
      endStyle,
      in: inProp,
      onExited,
      appear,
      enter,
      exit,
      ...other
    } = this.props;

    return (
      <div {...other} style={Object.assign({}, style, this.state.style)}>
        {children}
      </div>
    );
  }
}
