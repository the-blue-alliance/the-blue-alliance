import React, { Component } from 'react'
import PropTypes from 'prop-types'

import WEBCAST_SHAPE from '../../constants/ApiWebcast'

class WebcastItem extends Component {
  constructor(props) {
    super(props)
    this.onRemoveClick = this.onRemoveClick.bind(this)
  }

  onRemoveClick() {
    this.props.removeWebcast(this.props.index)
  }

  render() {
    let item = null
    if (this.props.webcast.url) {
      item = this.props.webcast.url
    } else {
      item = `${this.props.webcast.type} - ${this.props.webcast.channel}`
    }

    return (
      <p>{item} &nbsp;
        <button
          className="btn btn-danger"
          onClick={this.onRemoveClick}
        >
          Remove
        </button>
      </p>
    )
  }
}

WebcastItem.propTypes = {
  webcast: PropTypes.shape(WEBCAST_SHAPE).isRequired,
  index: PropTypes.number.isRequired,
  removeWebcast: PropTypes.func.isRequired,
}

export default WebcastItem
