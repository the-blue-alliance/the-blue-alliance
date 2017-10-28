import React from 'react'
import PropTypes from 'prop-types'
import WebcastItem from './WebcastItem'

import WEBCAST_SHAPE from '../../constants/ApiWebcast'

const WebcastList = (props) => (
  <div>
    {props.webcasts.length > 0 &&
    <p>
      {props.webcasts.length} webcasts found
    </p>
    }
    <ul>
      {props.webcasts.map((webcast, index) =>
        <li key={JSON.stringify(webcast)}>
          <WebcastItem
            webcast={webcast}
            removeWebcast={props.removeWebcast}
            index={index}
          />
        </li>)
      }
    </ul>
  </div>
)

WebcastList.propTypes = {
  webcasts: PropTypes.arrayOf(PropTypes.shape(WEBCAST_SHAPE)).isRequired,
  removeWebcast: PropTypes.func.isRequired,
}

export default WebcastList
