import React, { Component } from 'react'
import PropTypes from 'prop-types'
import WebcastItem from './WebcastItem'

import WEBCAST_SHAPE from '../../constants/ApiWebcast'

class WebcastList extends Component {

  render() {
    return (
      <div>
        {this.props.webcasts.length > 0 &&
        <p>
          {this.props.webcasts.length} webcasts found
        </p>
        }
        <ul>
          {this.props.webcasts.map(((webcast, index) =>
            <li key={JSON.stringify(webcast)}>
              <WebcastItem
                webcast={webcast}
                removeWebcast={this.props.removeWebcast}
                index={index}
              />
            </li>).bind(this))
          }
        </ul>
      </div>
    )
  }
}

WebcastList.propTypes = {
  webcasts: PropTypes.arrayOf(PropTypes.shape(WEBCAST_SHAPE)).isRequired,
  removeWebcast: PropTypes.func.isRequired,
}

export default WebcastList
