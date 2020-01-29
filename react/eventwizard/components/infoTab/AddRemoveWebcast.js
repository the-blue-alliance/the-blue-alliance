
import React, { Component } from 'react'
import PropTypes from 'prop-types'

import WebcastList from './WebcastList'
import EVENT_SHAPE from '../../constants/ApiEvent'

class AddRemoveWebcast extends Component {
  constructor(props) {
    super(props)
    this.state = {
      nextWebcastToAdd: '',
    }

    this.onNextWebcastChange = this.onNextWebcastChange.bind(this)
    this.onAddWebcastClick = this.onAddWebcastClick.bind(this)
  }

  onNextWebcastChange(event) {
    this.setState({ nextWebcastToAdd: event.target.value })
  }

  onAddWebcastClick() {
    this.props.addWebcast(this.state.nextWebcastToAdd)
    this.setState({ nextWebcastToAdd: '' })
  }

  render() {
    let webcastList = null
    if (this.props.eventInfo && this.props.eventInfo.webcasts.length > 0) {
      webcastList =
        (<WebcastList
          webcasts={this.props.eventInfo.webcasts}
          removeWebcast={this.props.removeWebcast}
        />)
    } else {
      webcastList = (<p>No webcasts found</p>)
    }

    return (
      <div className="form-group">
        <label htmlFor="webcast_list" className="col-sm-2 control-label">
          Webcasts
        </label>
        <div className="col-sm-10" id="webcast_list">
          {webcastList}

          <input
            type="text"
            id="webcast_url"
            placeholder="https://youtu.be/abc123"
            disabled={this.props.eventInfo === null}
            onChange={this.onNextWebcastChange}
            value={this.state.nextWebcastToAdd}
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
    )
  }
}

AddRemoveWebcast.propTypes = {
  eventInfo: PropTypes.shape(EVENT_SHAPE),
  addWebcast: PropTypes.func.isRequired,
  removeWebcast: PropTypes.func.isRequired,
}

export default AddRemoveWebcast
