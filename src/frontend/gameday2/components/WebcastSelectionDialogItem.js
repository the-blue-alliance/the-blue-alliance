import React from "react";
import PropTypes from "prop-types";
import { ListItem } from "material-ui/List";

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
      <ListItem
        primaryText={this.props.webcast.name}
        secondaryText={this.props.secondaryText}
        onClick={() => this.handleClick()}
        leftIcon={this.props.leftIcon}
        rightIcon={this.props.rightIcon}
        innerDivStyle={{
          paddingLeft: "50px", // Leave room for the left icon
        }}
      />
    );
  }
}
