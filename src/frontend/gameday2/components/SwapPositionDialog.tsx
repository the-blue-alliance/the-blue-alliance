import React from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import Dialog from "material-ui/Dialog";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import FlatButton from "material-ui/FlatButton";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'reac... Remove this comment to see the full error message
import EventListener from "react-event-listener";
import SwapPositionPreviewCell from "./SwapPositionPreviewCell";
import {
  NUM_VIEWS_FOR_LAYOUT,
  LAYOUT_STYLES,
} from "../constants/LayoutConstants";

type Props = {
  open: boolean;
  position: number;
  layoutId: number;
  swapWebcasts: (...args: any[]) => any;
  onRequestClose: (...args: any[]) => any;
};

export default class SwapPositionDialog extends React.Component<Props> {
  container: any;

  componentDidMount() {
    this.updateSizing();
  }

  componentDidUpdate() {
    this.updateSizing();
  }

  onRequestSwap(targetPosition: any) {
    this.props.swapWebcasts(this.props.position, targetPosition);
    this.onRequestClose();
  }

  onRequestClose() {
    if (this.props.onRequestClose) {
      this.props.onRequestClose();
    }
  }

  updateSizing() {
    const container = this.container;
    if (this.props.open && container) {
      const windowWidth = window.innerWidth;
      const windowHeight = window.innerHeight;
      const aspectRatio = windowWidth / windowHeight;

      const containerWidth = container.offsetWidth;
      const containerHeight = containerWidth / aspectRatio;

      container.style.height = `${containerHeight}px`;
    }
  }

  render() {
    const videoViews = [];
    const layoutId = this.props.layoutId;

    for (let i = 0; i < NUM_VIEWS_FOR_LAYOUT[layoutId]; i++) {
      const cellStyle = LAYOUT_STYLES[layoutId][i];

      videoViews.push(
        <SwapPositionPreviewCell
          key={i.toString()}
          style={cellStyle}
          enabled={i !== this.props.position}
          onClick={() => this.onRequestSwap(i)}
        />
      );
    }

    const actions = [
      <FlatButton
        label="Cancel"
        primary
        onClick={() => this.onRequestClose()}
      />,
    ];

    const bodyStyle = {
      padding: 8,
    };

    const previewContainerStyle = {
      padding: "4px",
      position: "relative",
    };

    return (
      <Dialog
        title="Select a position to swap with"
        actions={actions}
        modal={false}
        bodyStyle={bodyStyle}
        open={this.props.open}
        onRequestClose={() => this.onRequestClose()}
        autoScrollBodyContent
      >
        <EventListener target="window" onResize={() => this.updateSizing()} />
        <div
          // @ts-expect-error ts-migrate(2322) FIXME: Type '{ padding: string; position: string; }' is n... Remove this comment to see the full error message
          style={previewContainerStyle}
          ref={(e) => {
            this.container = e;
            this.updateSizing();
          }}
        >
          {videoViews}
        </div>
      </Dialog>
    );
  }
}
