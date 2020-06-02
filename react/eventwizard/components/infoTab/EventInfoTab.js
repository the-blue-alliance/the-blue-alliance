import React, { Component } from 'react'
import PropTypes from 'prop-types'
import Dialog from 'react-bootstrap-dialog'

import PlayoffTypeDropdown from './PlayoffTypeDropdown'
import SyncCodeInput from './SyncCodeInput'
import AddRemoveWebcast from './AddRemoveWebcast'
import AddRemoveTeamMap from './AddRemoveTeamMap'
import ensureRequestSuccess from '../../net/EnsureRequestSuccess'

class EventInfoTab extends Component {
  constructor(props) {
    super(props)
    this.state = {
      eventInfo: null,
      status: '',
      buttonClass: 'btn-primary',
    }

    this.loadEventInfo = this.loadEventInfo.bind(this)
    this.setPlayoffType = this.setPlayoffType.bind(this)
    this.updateEventInfo = this.updateEventInfo.bind(this)
    this.onFirstCodeChange = this.onFirstCodeChange.bind(this)
    this.addWebcast = this.addWebcast.bind(this)
    this.removeWebcast = this.removeWebcast.bind(this)
    this.addTeamMap = this.addTeamMap.bind(this)
    this.removeTeamMap = this.removeTeamMap.bind(this)
  }

  componentWillReceiveProps(newProps) {
    if (newProps.selectedEvent === null) {
      this.setState({ eventInfo: null, buttonClass: 'btn-primary' })
    } else if (newProps.selectedEvent !== this.props.selectedEvent) {
      this.loadEventInfo(newProps.selectedEvent)
      this.setState({ buttonClass: 'btn-primary' })
    }
  }

  onFirstCodeChange(event) {
    const currentInfo = this.state.eventInfo
    if (currentInfo !== null) {
      currentInfo.first_event_code = event.target.value
      this.setState({ eventInfo: currentInfo })
    }
  }

  setPlayoffType(newType) {
    const currentInfo = this.state.eventInfo
    if (currentInfo !== null) {
      currentInfo.playoff_type = newType.value
      this.setState({ eventInfo: currentInfo })
    }
  }

  loadEventInfo(newEventKey) {
    this.setState({ status: 'Loading event info...' })
    fetch(`/api/v3/event/${newEventKey}`, {
      credentials: 'same-origin',
    })
      .then(ensureRequestSuccess)
      .then((response) => (response.json()))
      .then((data1) => // Merge in remap_teams
        fetch(`/_/remap_teams/${newEventKey}`)
          .then(ensureRequestSuccess)
          .then((response) => (response.json()))
          .then((data2) => {
            const data = Object.assign({}, data1)
            data.remap_teams = data2
            return data
          })
      )
      .then((data) => (this.setState({ eventInfo: data, status: '' })))
  }

  addWebcast(webcastUrl) {
    const currentInfo = this.state.eventInfo
    if (currentInfo !== null) {
      currentInfo.webcasts.push({
        type: '',
        channel: '',
        url: webcastUrl,
      })
      this.setState({ eventInfo: currentInfo })
    }
  }

  removeWebcast(indexToRemove) {
    const currentInfo = this.state.eventInfo
    if (currentInfo !== null) {
      currentInfo.webcasts.splice(indexToRemove, 1)
      this.setState({ eventInfo: currentInfo })
    }
  }

  addTeamMap(fromTeamKey, toTeamKey) {
    const currentInfo = this.state.eventInfo
    if (currentInfo !== null) {
      currentInfo.remap_teams[fromTeamKey] = toTeamKey
      this.setState({ eventInfo: currentInfo })
    }
  }

  removeTeamMap(keyToRemove) {
    const currentInfo = this.state.eventInfo
    if (currentInfo !== null) {
      delete currentInfo.remap_teams[keyToRemove]
      this.setState({ eventInfo: currentInfo })
    }
  }

  updateEventInfo() {
    this.setState({ buttonClass: 'btn-warning' })
    this.props.makeTrustedRequest(
      `/api/trusted/v1/event/${this.props.selectedEvent}/info/update`,
      JSON.stringify(this.state.eventInfo),
      () => {
        this.setState({ buttonClass: 'btn-success' })
      },
      (error) => (this.dialog.showAlert(`${error}`))
    )
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

          <AddRemoveTeamMap
            eventInfo={this.state.eventInfo}
            addTeamMap={this.addTeamMap}
            removeTeamMap={this.removeTeamMap}
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
