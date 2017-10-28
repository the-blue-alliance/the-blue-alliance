import React, { Component } from 'react'
import PropTypes from 'prop-types'
import Dialog from 'react-bootstrap-dialog'

import PlayoffTypeDropdown from './PlayoffTypeDropdown'
import SyncCodeInput from './SyncCodeInput'
import AddRemoveWebcast from './AddRemoveWebcast'
import ensureRequestSuccess from '../../net/EnsureRequestSuccess'

class EventInfoTab extends Component {

  constructor(props) {
    super(props)
    this.state = {
      eventInfo: null,
      status: '',
      buttonClass: 'btn-primary'
    }

    this.loadEventInfo = this.loadEventInfo.bind(this)
    this.setPlayoffType = this.setPlayoffType.bind(this)
    this.updateEventInfo = this.updateEventInfo.bind(this)
    this.onFirstCodeChange = this.onFirstCodeChange.bind(this)
    this.addWebcast = this.addWebcast.bind(this)
    this.removeWebcast = this.removeWebcast.bind(this)
  }

  loadEventInfo(newEventKey) {
    this.setState({status: 'Loading event info...'})
    fetch(`/api/v3/event/${newEventKey}`, {
      credentials: 'same-origin',
    })
    .then(ensureRequestSuccess)
    .then((response) => (response.json()))
    .then((data) => (this.setState({eventInfo: data, status: ''})))
  }

  setPlayoffType(newType) {
    let currentInfo = this.state.eventInfo
    if (currentInfo !== null) {
      currentInfo.playoff_type = newType.value
      this.setState({eventInfo: currentInfo})
    }
  }

  onFirstCodeChange(event) {
    let currentInfo = this.state.eventInfo
    if (currentInfo !== null) {
      currentInfo.first_event_code = event.target.value
      this.setState({eventInfo: currentInfo})
    }
  }

  addWebcast(webcast_url) {
    let currentInfo = this.state.eventInfo
    if (currentInfo !== null) {
      currentInfo.webcasts.push({
        'type': '',
        'channel': '',
        'url': webcast_url,
      })
      this.setState({eventInfo: currentInfo})
    }
  }

  removeWebcast(index_to_remove) {
    let currentInfo = this.state.eventInfo
    if (currentInfo !== null) {
      currentInfo.webcasts.splice(index_to_remove, 1)
      this.setState({eventInfo: currentInfo})
    }
  }

  updateEventInfo() {
    this.setState({buttonClass: 'btn-warning'})
    this.props.makeTrustedRequest(
      `/api/trusted/v1/event/${this.props.selectedEvent}/info/update`,
      JSON.stringify(this.state.eventInfo),
      () => {
        this.setState({ buttonClass: 'btn-success' })
      },
      (error) => (this.dialog.showAlert(`${error}`))
    )
  }

  componentWillReceiveProps(newProps) {
    if (newProps.selectedEvent === null) {
      this.setState({eventInfo: null, buttonClass: 'btn-primary'})
    } else if (newProps.selectedEvent !== this.props.selectedEvent) {
      this.loadEventInfo(newProps.selectedEvent)
      this.setState({buttonClass: 'btn-primary'})
    }
  }

  render() {
    return (
      <div className="tab-pane" id="info">
        <h3>Event Info</h3>
        <Dialog ref={(dialog) => (this.dialog = dialog)} />
        {this.state.status &&
          <p>{this.state.status}</p>
        }
        <div className="row">
          <PlayoffTypeDropdown
            eventInfo={this.state.eventInfo}
            setType={this.setPlayoffType}
          />

          <SyncCodeInput
            eventInfo={this.state.eventInfo}
            setSyncCode={this.onFirstCodeChange}
          />

          <AddRemoveWebcast
            eventInfo={this.state.eventInfo}
            addWebcast={this.addWebcast}
            removeWebcast={this.removeWebcast}
          />

          <button
            className={`btn ${this.state.buttonClass}`}
            onClick={this.updateEventInfo}
            disabled={this.state.eventInfo === null}
          >
            Publish Changes
          </button>
        </div>
      </div>
    )
  }
}

EventInfoTab.propTypes = {
  selectedEvent: PropTypes.string,
  makeTrustedRequest: PropTypes.func.isRequired,
}

export default EventInfoTab
