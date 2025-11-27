import React from "react";
import PropTypes from "prop-types";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import SwapPositionPreviewCell from "./SwapPositionPreviewCell";
import {
  NUM_VIEWS_FOR_LAYOUT,
  LAYOUT_STYLES,
} from "../constants/LayoutConstants";

export default class SwapPositionDialog extends React.Component {
  static propTypes = {
    open: PropTypes.bool.isRequired,
    position: PropTypes.number.isRequired,
    layoutId: PropTypes.number.isRequired,
    swapWebcasts: PropTypes.func.isRequired,
    onRequestClose: PropTypes.func.isRequired,
  };

  componentDidMount() {
    this.updateSizing();
    this._boundUpdateSizing = this.updateSizing.bind(this);
    window.addEventListener("resize", this._boundUpdateSizing);
  }

  componentDidUpdate() {
    this.updateSizing();
  }

  onRequestSwap(targetPosition) {
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

  componentWillUnmount() {
    if (this._boundUpdateSizing) {
      window.removeEventListener("resize", this._boundUpdateSizing);
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
      <Button
        key="cancel"
        onClick={() => this.onRequestClose()}
        color="primary"
      >
        Cancel
      </Button>,
    ];

    const bodyStyle = {
      padding: 8,
    };

    const previewContainerStyle = {
      padding: "4px",
      position: "relative",
    };

    return (
      <Dialog open={this.props.open} onClose={() => this.onRequestClose()}>
        <DialogTitle>Select a position to swap with</DialogTitle>
        <DialogContent dividers style={bodyStyle}>
          {/* resize listener handled in lifecycle methods */}
          <div
            style={previewContainerStyle}
            ref={(e) => {
              this.container = e;
              this.updateSizing();
            }}
          >
            {videoViews}
          </div>
        </DialogContent>
        <DialogActions>{actions}</DialogActions>
      </Dialog>
    );
  }
}
