import React, { PropTypes } from 'react'
import LayoutDropdownItem from './LayoutDropdownItem'

export default React.createClass({
  propTypes: {
    setLayout: PropTypes.func.isRequired,
  },
  layoutSelected(layoutId) {
    this.props.setLayout(layoutId)
  },
  render() {
    return (
      <li className="dropdown">
        <a href="#" className="dropdown-toggle" data-toggle="dropdown">Set Layout <b className="caret" /></a>
        <ul className="dropdown-menu">
          <LayoutDropdownItem handleClick={this.layoutSelected} layoutId={0}>Single View</LayoutDropdownItem>
          <LayoutDropdownItem handleClick={this.layoutSelected} layoutId={1}>Split View</LayoutDropdownItem>
          <LayoutDropdownItem handleClick={this.layoutSelected} layoutId={2}>"1+2" View</LayoutDropdownItem>
          <LayoutDropdownItem handleClick={this.layoutSelected} layoutId={3}>Quad View</LayoutDropdownItem>
          <LayoutDropdownItem handleClick={this.layoutSelected} layoutId={4}>"1+3" View</LayoutDropdownItem>
          <LayoutDropdownItem handleClick={this.layoutSelected} layoutId={5}>"1+4" View</LayoutDropdownItem>
          <LayoutDropdownItem handleClick={this.layoutSelected} layoutId={6}>Hex View</LayoutDropdownItem>
          <LayoutDropdownItem handleClick={this.layoutSelected} layoutId={7}>Octo-View</LayoutDropdownItem>
          <LayoutDropdownItem handleClick={this.layoutSelected} layoutId={8}>Nona-View</LayoutDropdownItem>
        </ul>
      </li>
    )
  },
})
