import React, { Component } from 'react'
import PropTypes from 'prop-types'

class AddTeamsFMSReport extends Component {

  constructor(props) {
    super(props)
    this.state = {
      buttonClass: 'btn-primary'
    }
  }

  render() {
    return (
      <div>
        <h4>Import FMS Report</h4>
      </div>
    )
  }
}

AddTeamsFMSReport.propTypes = {
  selectedEvent: PropTypes.string,
  makeTrustedRequest: PropTypes.func.isRequired,
  clearTeams: PropTypes.func,
  showErrorMessage: PropTypes.func.isRequired,
}

export default AddTeamsFMSReport
