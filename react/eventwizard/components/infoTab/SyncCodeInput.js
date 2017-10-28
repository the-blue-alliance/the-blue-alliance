
import React, { Component } from 'react'
import PropTypes from 'prop-types'
import Select from 'react-select'

import EVENT_SHAPE from '../../constants/ApiEvent'

class SyncCodeInput extends Component {

  render() {
    return (
      <div className="form-group">
        <label htmlFor="first_code" className="col-sm-2 control-label">
          FIRST Sync Code
        </label>
        <div className="col-sm-10">
        <input
          type="text"
          className="form-control"
          id="first_code"
          placeholder="IRI"
          value={this.props.eventInfo ? this.props.eventInfo.first_sync_code : ''}
          disabled={this.props.eventInfo === null}
          onChange={this.props.setSyncCode}
          />
        </div>
      </div>
    )
  }
}

SyncCodeInput.propTypes = {
  eventInfo: PropTypes.shape(EVENT_SHAPE),
  setSyncCode: PropTypes.func.isRequired,
}

export default SyncCodeInput
