import React, { PropTypes } from 'react'
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem'

const WebcastListItem = React.createClass({
  propTypes: {
    addWebcast: PropTypes.func.isRequired,
  },
  handleClick() {
    this.props.addWebcast(this.props.webcast.id)
  },
  render() {
    return <BootstrapNavDropdownListItem handleClick={this.handleClick}>{this.props.webcast.name}</BootstrapNavDropdownListItem>
  },
})

export default WebcastListItem
