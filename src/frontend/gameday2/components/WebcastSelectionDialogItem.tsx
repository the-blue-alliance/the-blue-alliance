import React from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
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
