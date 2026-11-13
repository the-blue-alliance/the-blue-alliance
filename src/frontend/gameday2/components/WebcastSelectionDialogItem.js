import React from "react";
import PropTypes from "prop-types";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import ListItemIcon from "@mui/material/ListItemIcon";

export default class WebcastSelectionDialogItem extends React.Component {
  static propTypes = {
    webcast: PropTypes.object.isRequired,
    webcastSelected: PropTypes.func.isRequired,
    secondaryText: PropTypes.string,
    leftIcon: PropTypes.element,
    rightIcon: PropTypes.any,
  };

  handleClick() {
    this.props.webcastSelected(this.props.webcast.id);
  }

  render() {
    return (
      <ListItem disablePadding secondaryAction={this.props.rightIcon}>
        <ListItemButton onClick={() => this.handleClick()}>
          {this.props.leftIcon && (
            <ListItemIcon>{this.props.leftIcon}</ListItemIcon>
          )}
          <ListItemText
            primary={this.props.webcast.name}
            secondary={this.props.secondaryText}
          />
        </ListItemButton>
      </ListItem>
    );
  }
}
