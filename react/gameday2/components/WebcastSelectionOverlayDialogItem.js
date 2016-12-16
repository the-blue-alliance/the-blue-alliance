import React, { PropTypes } from 'react'
import { ListItem } from 'material-ui/List'

export default class WebcastSelectionOverlayDialogItem extends React.Component {
  static propTypes = {
    webcast: PropTypes.object.isRequired,
    webcastSelected: PropTypes.func.isRequired,
  }

  handleClick() {
    this.props.webcastSelected(this.props.webcast.id)
  }

  render() {
    return (
      <ListItem
        primaryText={this.props.webcast.name}
        onTouchTap={() => this.handleClick()}
      />
    )
  }
}
