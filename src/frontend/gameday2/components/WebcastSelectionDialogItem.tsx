import React from "react";
import { ListItem } from "material-ui/List";

type Props = {
  webcast: any;
  webcastSelected: (...args: any[]) => any;
  secondaryText?: string;
  rightIcon?: any;
};

export default class WebcastSelectionDialogItem extends React.Component<Props> {
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
