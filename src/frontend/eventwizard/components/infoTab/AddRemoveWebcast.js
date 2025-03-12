import React, { Component } from "react";
import PropTypes from "prop-types";

import WebcastList from "./WebcastList";
import EVENT_SHAPE from "../../constants/ApiEvent";

class AddRemoveWebcast extends Component {
  constructor(props) {
    super(props);
    this.state = {
      newWebcastUrl: "",
      newWebcastDate: "",
    };

    this.onNewWebcastUrlChange = this.onNewWebcastUrlChange.bind(this);
    this.onNewWebcastDateChange = this.onNewWebcastDateChange.bind(this);
    this.onAddWebcastClick = this.onAddWebcastClick.bind(this);
  }

  onNewWebcastUrlChange(event) {
    this.setState({ newWebcastUrl: event.target.value });
  }

  onNewWebcastDateChange(event) {
    this.setState({ newWebcastDate: event.target.value });
  }

  onAddWebcastClick() {
    this.props.addWebcast(this.state.newWebcastUrl, this.state.newWebcastDate);
    this.setState({
      newWebcastUrl: "",
      newWebcastDate: "",
    });
  }

  render() {
    let webcastList = null;
    if (this.props.eventInfo && this.props.eventInfo.webcasts.length > 0) {
      webcastList = (
        <WebcastList
          webcasts={this.props.eventInfo.webcasts}
          removeWebcast={this.props.removeWebcast}
        />
      );
    } else {
      webcastList = <p>No webcasts found</p>;
    }

    return (
      <div className="form-group row">
        <label htmlFor="webcast_list" className="col-sm-2 control-label">
          Webcasts
        </label>
        <div className="col-sm-10" id="webcast_list">
          {webcastList}

          <div style={{ display: "flex", gap: "0.5em" }}>
            <input
              type="text"
              className="form-control"
              id="webcast_url"
              placeholder="https://youtu.be/abc123"
              disabled={this.props.eventInfo === null}
              onChange={this.onNewWebcastUrlChange}
              value={this.state.newWebcastUrl}
            />
            <input
              type="text"
              className="form-control"
              id="webcast_date"
              placeholder="2025-03-02 (optional)"
              disabled={this.props.eventInfo === null}
              onChange={this.onNewWebcastDateChange}
              value={this.state.newWebcastDate}
            />
            <button
              className="btn btn-info"
              onClick={this.onAddWebcastClick}
              disabled={this.props.eventInfo === null}
            >
              Add Webcast
            </button>
          </div>
        </div>
      </div>
    );
  }
}

AddRemoveWebcast.propTypes = {
  eventInfo: PropTypes.shape(EVENT_SHAPE),
  addWebcast: PropTypes.func.isRequired,
  removeWebcast: PropTypes.func.isRequired,
};

export default AddRemoveWebcast;
