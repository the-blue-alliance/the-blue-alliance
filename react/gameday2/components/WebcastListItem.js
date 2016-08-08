import React, { PropTypes } from 'react'
import BootstrapNavDropdownListItem from './BootstrapNavDropdownListItem'
import { WebcastPropType } from '../utils/webcastUtils'

export default React.createClass({
  propTypes: {
    webcast: WebcastPropType.isRequired,
    addWebcast: PropTypes.func.isRequired,
  },
  handleClick() {
    this.props.addWebcast(this.props.webcast.id)
  },
  render() {
    return <BootstrapNavDropdownListItem handleClick={this.handleClick}>{this.props.webcast.name}</BootstrapNavDropdownListItem>
  },
})
