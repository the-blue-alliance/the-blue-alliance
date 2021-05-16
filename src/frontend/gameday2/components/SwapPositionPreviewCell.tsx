import React from "react";

function getStyles(props: any, state: any) {
  let backgroundColor;
  if (props.enabled) {
    if (state.hovered) {
      backgroundColor = "#aaaaaa";
    } else {
      backgroundColor = "#cccccc";
    }
  } else {
    backgroundColor = "#555555";
  }

  const style = {
    padding: "4px",
    backgroundClip: "content-box",
    backgroundColor,
    cursor: props.enabled ? "pointer" : null,
  };

  return Object.assign({}, style, props.style);
}

type Props = {
  style: any;
  enabled: boolean;
  onClick: (...args: any[]) => any;
};

type State = any;

export default class SwapPositionPreviewCell extends React.Component<
  Props,
  State
> {
  constructor(props: Props) {
    super(props);

    this.state = {
      hovered: false,
    };
  }

  onMouseOver() {
    this.setState({
      hovered: true,
    });
  }

  onMouseOut() {
    this.setState({
      hovered: false,
    });
  }

  onClick() {
    if (this.props.onClick) {
      this.props.onClick();
    }
  }

  render() {
    const styles = getStyles(this.props, this.state);

    return (
      <div
        style={styles}
        onMouseOver={() => this.onMouseOver()}
        onMouseOut={() => this.onMouseOut()}
        onClick={() => this.onClick()}
      />
    );
  }
}
