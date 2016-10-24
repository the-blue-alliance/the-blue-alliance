import React, { PropTypes } from 'react'
import NativeListener from 'react-native-listener'
import classNames from 'classnames'

export default React.createClass({
  propTypes: {
    children: PropTypes.node,
    checked: PropTypes.bool.isRequired,
    handleClick: PropTypes.func,
  },
  handleClick(event) {
    if (this.props.handleClick) {
      // If a callback to handle the click is given, prevent the default behavior
      event.preventDefault()
      event.stopPropagation()
      this.props.handleClick()
    }
  },
  render() {
    const checkmarkClasses = classNames({
      hidden: !this.props.checked,
      'glyphicon glyphicon-ok': true,
      'pull-right': true,
    })
    return (
      <NativeListener onClick={this.handleClick}>
        <li><button href={'#'} onClick={this.handleClick}>{this.props.children} <span className={checkmarkClasses} /></button></li>
      </NativeListener>
    )
  },
})
