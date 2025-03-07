import React, { Component } from "react";
import PropTypes from "prop-types";
import AsyncSelect from "react-select/async";

class EventSelector extends Component {
  static eventsCache;

  static async loadEvents(search) {
    if (!EventSelector.eventsCache) {
      EventSelector.eventsCache = await fetch("/_/account/apiwrite_events", {
        credentials: "same-origin",
      })
        .then((response) => response.json())
        .then((events) => {
          events.push({ value: "_other", label: "Other" });
          return events;
        });
    }

    return EventSelector.eventsCache.filter((e) =>
      e.label.toLowerCase().includes(search.toLowerCase())
    );
  }

  constructor(props) {
    super(props);
    this.state = {
      eventSelectLabel: "",
    };
    this.onEventSelected = this.onEventSelected.bind(this);
    this.onManualEventChange = this.onManualEventChange.bind(this);
  }

  onEventSelected(newEvent) {
    this.props.clearAuth();
    this.setState({ eventSelectLabel: newEvent.label });

    if (newEvent.value === "_other") {
      this.props.setManualEvent(true);
      this.props.setEvent("");
    } else {
      this.props.setManualEvent(false);
      this.props.setEvent(newEvent.value);
    }
  }

  onManualEventChange(event) {
    this.props.setEvent(event.target.value);
  }

  render() {
    let eventKeyBox;
    if (this.props.manualEvent) {
      eventKeyBox = (
        <input
          type="text"
          className="form-control"
          id="event_key"
          placeholder="Event Key"
          onChange={this.onManualEventChange}
        />
      );
    }

    return (
      <div className="form-group">
        <label htmlFor="event_key_select" className="col-sm-2 control-label">
          Select Event
        </label>
        <div className="col-sm-10">
          <AsyncSelect
            name="selectEvent"
            placeholder="Select an Event..."
            loadingPlaceholder="Loading Events..."
            value={
              this.state.eventSelectLabel && {
                label: this.state.eventSelectLabel,
              }
            }
            loadOptions={EventSelector.loadEvents}
            onChange={this.onEventSelected}
            defaultOptions
          />
          {eventKeyBox}
        </div>
      </div>
    );
  }
}

EventSelector.propTypes = {
  manualEvent: PropTypes.bool.isRequired,
  setEvent: PropTypes.func.isRequired,
  setManualEvent: PropTypes.func.isRequired,
  clearAuth: PropTypes.func.isRequired,
};

export default EventSelector;
