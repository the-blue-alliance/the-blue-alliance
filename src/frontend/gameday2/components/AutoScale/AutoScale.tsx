import React, { Component } from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'elem... Remove this comment to see the full error message
import ere from "element-resize-event";

type OwnProps = {
  wrapperClass?: string;
  containerClass?: string;
  contentClass?: string;
  maxHeight?: number;
  maxWidth?: number;
  maxScale?: number;
};

type State = any;

type Props = OwnProps & typeof AutoScale.defaultProps;

export default class AutoScale extends Component<Props, State> {
  static defaultProps = {
    wrapperClass: "",
    containerClass: "",
    contentClass: "",
  };

  content: any;
  wrapper: any;

  constructor() {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1-2 arguments, but got 0.
    super();

    this.state = {
      wrapperSize: { width: 0, height: 0 },
      contentSize: { width: 0, height: 0 },
      scale: 1,
    };
  }

  componentDidMount() {
    const actualContent = this.content.children[0];

    this.updateState({
      ...this.state,
      contentSize: {
        width: actualContent.offsetWidth,
        height: actualContent.offsetHeight,
      },
      wrapperSize: {
        width: this.wrapper.offsetWidth,
        height: this.wrapper.offsetHeight,
      },
    });

    ere(actualContent, () => {
      this.updateState({
        ...this.state,
        contentSize: {
          width: actualContent.offsetWidth,
          height: actualContent.offsetHeight,
        },
      });
    });

    ere(this.wrapper, () => {
      this.updateState({
        ...this.state,
        wrapperSize: {
          width: this.wrapper.offsetWidth,
          height: this.wrapper.offsetHeight,
        },
      });
    });
  }

  updateState(newState: any) {
    const { maxHeight, maxWidth, maxScale } = this.props;
    const { wrapperSize, contentSize } = newState;

    let scale = Math.min(
      wrapperSize.width / contentSize.width,
      wrapperSize.height / contentSize.height
    );

    if (maxHeight) {
      scale = Math.min(scale, maxHeight / contentSize.height);
    }
    if (maxWidth) {
      scale = Math.min(scale, maxWidth / contentSize.width);
    }
    if (maxScale) {
      scale = Math.min(scale, maxScale);
    }

    this.setState({
      ...newState,
      scale,
    });
  }

  render() {
    const { scale, contentSize } = this.state;
    const { children, wrapperClass, containerClass, contentClass } = this.props;
    const containerHeight = scale * contentSize.height;
    const containerWidth = scale * contentSize.width;

    return (
      <div
        ref={(el) => {
          this.wrapper = el;
        }}
        className={wrapperClass}
      >
        <div
          className={containerClass}
          style={{
            maxWidth: "100%",
            overflow: "hidden",
            width: `${containerWidth}px`,
            height: `${containerHeight}px`,
          }}
        >
          <div
            ref={(el) => {
              this.content = el;
            }}
            className={contentClass}
            style={{ transform: `scale(${scale})`, transformOrigin: "0 0 0" }}
          >
            {React.Children.only(children)}
          </div>
        </div>
      </div>
    );
  }
}
