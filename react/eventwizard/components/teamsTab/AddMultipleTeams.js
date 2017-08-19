import React, { Component } from 'react'
import PropTypes from 'prop-types'

class AddMultipleTeams extends Component {

  constructor(props) {
    super(props)
    this.state = {
      inputTeams: '',
      buttonClass: 'btn-primary'
    }
    this.addTeams = this.addTeams.bind(this)
    this.onInputChange = this.onInputChange.bind(this)
  }

  onInputChange(event) {
    this.setState({inputTeams: event.target.value})
  }

  addTeams() {
    if (!this.props.selectedEvent) {
      // No valid event
      this.props.showErrorMessage('Please select an event before adding teams')
      return
    }

    var teams = this.state.inputTeams.split("\n");
    for (var i = 0; i < teams.length; i++) {
        var teamNum = parseInt(teams[i]);
        if(!teamNum || isNaN(teamNum) || teamNum <= 0 || teamNum > 9999){
          this.props.showErrorMessage("Invalid team "+teams[i]);
          return
        }
        teams[i] = "frc"+teamNum;
    }

    this.setState({buttonClass: 'btn-warning'})
    this.props.makeTrustedRequest(
      '/api/trusted/v1/event/'+this.props.selectedEvent+'/team_list/update',
      JSON.stringify(teams),
      () => {
        this.setState({buttonClass: 'btn-success'})
        this.props.clearTeams()
      },
      (error) => (this.props.showErrorMessage(`${error}`))
    )
  }

  render() {
    return (
      <div>
        <h4>Add Multiple Teams</h4>
            <p>Enter a list of team numbers, one per line. This will <em>overwrite</em> all existing teams for this event.</p>
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
  makeTrustedRequest: PropTypes.func.isRequired,
  showErrorMessage: PropTypes.func.isRequired,
}

export default AddMultipleTeams
