import React, { Component } from 'react'
import PropTypes from 'prop-types'
import Select from 'react-select'

import EVENT_SHAPE from '../../constants/ApiEvent'

class PlayoffTypeDropdown extends Component {
  static loadPlayoffTypes() {
    return fetch('/_/playoff_types', {
      credentials: 'same-origin',
    })
      .then((response) => (response.json()))
      .then((types) => ({ options: types }))
  }

  render() {
    return (
      <div className="form-group">
        <label htmlFor="selectType" className="col-sm-2 control-label">
          Playoff Type
        </label>
        <div className="col-sm-10">
          <Select.Async
            name="selectType"
            placeholder="Choose playoff type..."
            loadingPlaceholder="Loading playoff types..."
            clearable={false}
            searchable={false}
            value={this.props.eventInfo && this.props.eventInfo.playoff_type}
            loadOptions={PlayoffTypeDropdown.loadPlayoffTypes}
            onChange={this.props.setType}
            disabled={this.props.eventInfo === null}
          />
        </div>
      </div>
    )
  }
}

PlayoffTypeDropdown.propTypes = {
  eventInfo: PropTypes.shape(EVENT_SHAPE),
  setType: PropTypes.func.isRequired,
}

export default PlayoffTypeDropdown
