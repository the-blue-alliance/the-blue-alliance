import React, { Component } from "react";
import PropTypes from "prop-types";
import AsyncSelect from "react-select/async";

import EVENT_SHAPE from "../../constants/ApiEvent";

class PlayoffTypeDropdown extends Component {
  static loadPlayoffTypes() {
    return fetch("/_/playoff_types", {
      credentials: "same-origin",
    }).then((response) => response.json());
  }

  render() {
    return (
      <div className="form-group">
        <label htmlFor="selectType" className="col-sm-2 control-label">
          Playoff Type
        </label>
        <div className="col-sm-10">
          <AsyncSelect
            name="selectType"
            placeholder="Choose playoff type..."
            loadingPlaceholder="Loading playoff types..."
            clearable={false}
            searchable={false}
            value={
              this.props.eventInfo && {
                label: this.props.eventInfo.playoff_type_string,
              }
            }
            loadOptions={PlayoffTypeDropdown.loadPlayoffTypes}
            onChange={this.props.setType}
            isDisabled={this.props.eventInfo === null}
            defaultOptions
          />
        </div>
      </div>
    );
  }
}

PlayoffTypeDropdown.propTypes = {
  eventInfo: PropTypes.shape(EVENT_SHAPE),
  setType: PropTypes.func.isRequired,
};

export default PlayoffTypeDropdown;
