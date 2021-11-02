import React from "react";

type Props = {
  beginStyle: any;
  endStyle: any;
  style?: any;
};

type State = any;

export default class AnimatableContainer extends React.Component<Props, State> {
  enterTimeout: any;
  leaveTimeout: any;

  constructor(props: Props) {
    super(props);

    this.state = {
      style: props.beginStyle,
    };
  }

  componentWillUnmount() {
    clearTimeout(this.enterTimeout);
    clearTimeout(this.leaveTimeout);
  }

  componentWillEnter(callback: any) {
    this.componentWillAppear(callback);
  }

  componentWillAppear(callback: any) {
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

  componentWillLeave(callback: any) {
    this.setState({
      style: this.props.beginStyle,
    });

    this.leaveTimeout = setTimeout(callback, 300);
  }

  render() {
    /* eslint-disable no-unused-vars */
    // beginStyle and endStyle are unused, but we exclude them from ...other so
    // they don't get passed as props to our div
    const { style, children, beginStyle, endStyle, ...other } = this.props;

    return (
      <div {...other} style={Object.assign({}, style, this.state.style)}>
        {children}
      </div>
    );
  }
}
