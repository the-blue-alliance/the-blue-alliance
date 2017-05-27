import React, { Component } from 'react'
import PropTypes from 'prop-types'
import EventSelectorContainer from '../containers/EventSelectorContainer'
import AuthInputContainer from '../containers/AuthInputContainer'
import AuthToolsContainer from '../containers/AuthToolsContainer'

class SetupFrame extends Component {

  render() {
    return (
      <div>
        <h2 id="setup">Setup</h2>
        <form className="form-horizontal" role="form">
          <EventSelectorContainer />
          <AuthToolsContainer />
          <AuthInputContainer />
        </form>
      </div>
    )
  }
}

export default SetupFrame