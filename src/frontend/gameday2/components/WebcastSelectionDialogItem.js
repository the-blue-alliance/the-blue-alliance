import { ListItem } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

export default class WebcastSelectionDialogItem extends React.Component {
  static propTypes = {
    webcast: PropTypes.object.isRequired,
    webcastSelected: PropTypes.func.isRequired,
    secondaryText: PropTypes.string,
    rightIcon: PropTypes.any,
  };

  handleClick() {
    this.props.webcastSelected(this.props.webcast.id);
  }

  render() {
    return (
      <ListItem
        primaryText={this.props.webcast.name}
        secondaryText={this.props.secondaryText}
        onClick={() => this.handleClick()}
        rightIcon={this.props.rightIcon}
      />
    );
  }
}
