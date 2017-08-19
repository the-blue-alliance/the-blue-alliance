import React, { Component } from 'react'
import PropTypes from 'prop-types'
import { Typeahead } from 'react-bootstrap-typeahead'

class AddRemoveSingleTeam extends Component {

  constructor(props) {
    super(props)
    this.state = {
      teamTypeaheadOptions: [],
      addButtonClass: 'btn-primary',
      removeButtonClass: 'btn-primary'
    }
    this.addSingleTeam = this.addSingleTeam.bind(this)
    this.removeSingleTeam = this.removeSingleTeam.bind(this)
  }

  componentDidMount() {
    // Load team typeahead data
    fetch('/_/typeahead/teams-all')
      .then(resp => resp.json())
      .then(json => this.setState({teamTypeaheadOptions: json}))
  }

  addSingleTeam() {
    this.props.showErrorMessage('TODO: Implement API to add single team');
    this.setState({addSingleButtonStatus: 'btn-danger'});
  }

  removeSingleTeam() {
    this.props.showErrorMessage('TODO: Implement API to remove single team');
    this.setState({addSingleButtonStatus: 'btn-danger'});
  }

  render() {
    return (
      <div>
        <h4>Add/Remove Single Team</h4>
        <Typeahead
          placeholder="Enter team name or number..."
          options={this.state.teamTypeaheadOptions}
        />
        <button
          className={`btn ${this.state.addButtonClass}`}
          onClick={this.addSingleTeam}
          disabled={!this.props.selectedEvent}
        >
          Add Team
        </button>
        <button
          className={`btn ${this.state.removeButtonClass}`}
          onClick={this.removeSingleTeam}
          disabled={!this.props.selectedEvent}
        >
          Remove Team
        </button>
      </div>
    )
  }
}

AddRemoveSingleTeam.propTypes = {
  selectedEvent: PropTypes.string,
  makeTrustedRequest: PropTypes.func.isRequired,
  clearTeams: PropTypes.func,
  showErrorMessage: PropTypes.func.isRequired,
}

export default AddRemoveSingleTeam
