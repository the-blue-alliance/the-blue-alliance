import React, { Component } from 'react'
import PropTypes from 'prop-types'

class AddMultipleTeams extends Component {
  constructor(props) {
    super(props)
    this.state = {
      inputTeams: '',
      buttonClass: 'btn-primary',
    }
    this.addTeams = this.addTeams.bind(this)
    this.onInputChange = this.onInputChange.bind(this)
  }

  onInputChange(event) {
    this.setState({ inputTeams: event.target.value })
  }

  addTeams() {
    if (!this.props.selectedEvent) {
      // No valid event
      this.props.showErrorMessage('Please select an event before adding teams')
      return
    }

    const teams = []
    const teamInput = this.state.inputTeams.split('\n')
    for (let i = 0; this.state.inputTeams && i < teamInput.length; i++) {
      const teamNum = parseInt(teamInput[i], 10)
      if (!teamNum || isNaN(teamNum) || teamNum <= 0 || teamNum > 9999) {
        this.props.showErrorMessage(`Invalid team ${teams[i]}`)
        return
      }
      teams.push(`frc${teamNum}`)
    }

    this.setState({ buttonClass: 'btn-warning' })
    this.props.updateTeamList(
      teams,
      () => {
        this.setState({ buttonClass: 'btn-success' })
        this.props.clearTeams()
      },
      (error) => (this.props.showErrorMessage(`${error}`))
    )
  }

  render() {
    return (
      <div>
        <h4>Add Multiple Teams</h4>
        <p>Enter a list of team numbers, one per line. This will <em>overwrite</em> all existing
          teams for this event.</p>
        <textarea
          className="form-control"
          value={this.state.inputTeams}
          onChange={this.onInputChange}
        />
        <button
          className={`btn ${this.state.buttonClass}`}
          onClick={this.addTeams}
          disabled={!this.props.selectedEvent}
        >
              Overwrite Teams
        </button>
      </div>
    )
  }
}

AddMultipleTeams.propTypes = {
  selectedEvent: PropTypes.string,
  clearTeams: PropTypes.func,
  updateTeamList: PropTypes.func.isRequired,
  showErrorMessage: PropTypes.func.isRequired,
}

export default AddMultipleTeams
