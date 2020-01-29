import React, { Component } from 'react'
import PropTypes from 'prop-types'
import Select from 'react-select'

class EventSelector extends Component {
  static loadEvents() {
    return fetch('/_/account/apiwrite_events', {
      credentials: 'same-origin',
    })
      .then((response) => (
        response.json()
      ))
      .then((events) => {
        events.push({ value: '_other', label: 'Other' })
        return { options: events }
      })
  }

  constructor(props) {
    super(props)
    this.state = {
      eventSelectValue: '',
    }
    this.onEventSelected = this.onEventSelected.bind(this)
    this.onManualEventChange = this.onManualEventChange.bind(this)
  }

  onEventSelected(newEvent) {
    this.props.clearAuth()
    this.setState({ eventSelectValue: newEvent.value })

    if (newEvent.value === '_other') {
      this.props.setManualEvent(true)
      this.props.setEvent('')
    } else {
      this.props.setManualEvent(false)
      this.props.setEvent(newEvent.value)
    }
  }

  onManualEventChange(event) {
    this.props.setEvent(event.target.value)
  }

  render() {
    let eventKeyBox
    if (this.props.manualEvent) {
      eventKeyBox = (
        <input
          type="text"
          className="form-control"
          id="event_key"
          placeholder="Event Key"
          onChange={this.onManualEventChange}
        />
      )
    }

    return (
      <div className="form-group">
        <label htmlFor="event_key_select" className="col-sm-2 control-label">Select Event</label>
        <div className="col-sm-10">
          <Select.Async
            name="selectEvent"
            placeholder="Select an Event..."
            loadingPlaceholder="Loading Events..."
            clearable={false}
            searchable={false}
            value={this.state.eventSelectValue}
            loadOptions={EventSelector.loadEvents}
            onChange={this.onEventSelected}
          />
          {eventKeyBox}
        </div>
      </div>
    )
  }
}

EventSelector.propTypes = {
  manualEvent: PropTypes.bool.isRequired,
  setEvent: PropTypes.func.isRequired,
  setManualEvent: PropTypes.func.isRequired,
  clearAuth: PropTypes.func.isRequired,
}

export default EventSelector
