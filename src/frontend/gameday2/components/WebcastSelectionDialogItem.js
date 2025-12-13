import React from "react";
import PropTypes from "prop-types";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemSecondaryAction from "@mui/material/ListItemSecondaryAction";

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
      <ListItem button onClick={() => this.handleClick()}>
        {this.props.leftIcon && (
          <ListItemIcon>{this.props.leftIcon}</ListItemIcon>
        )}
        <ListItemText
          primary={this.props.webcast.name}
          secondary={this.props.secondaryText}
        />
        {this.props.rightIcon && (
          <ListItemSecondaryAction>
            {this.props.rightIcon}
          </ListItemSecondaryAction>
        )}
      </ListItem>
    );
  }
}
