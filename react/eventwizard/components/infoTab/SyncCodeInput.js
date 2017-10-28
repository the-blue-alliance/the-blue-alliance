
import React from 'react'
import PropTypes from 'prop-types'

import EVENT_SHAPE from '../../constants/ApiEvent'

const SyncCodeInput = (props) => (
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
        value={props.eventInfo && props.eventInfo.first_event_code}
        disabled={props.eventInfo === null}
        onChange={props.setSyncCode}
      />
    </div>
  </div>
)

SyncCodeInput.propTypes = {
  eventInfo: PropTypes.shape(EVENT_SHAPE),
  setSyncCode: PropTypes.func.isRequired,
}

export default SyncCodeInput
