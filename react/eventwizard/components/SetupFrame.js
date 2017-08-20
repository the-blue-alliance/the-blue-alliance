import React from 'react'
import EventSelectorContainer from '../containers/EventSelectorContainer'
import AuthInputContainer from '../containers/AuthInputContainer'
import AuthToolsContainer from '../containers/AuthToolsContainer'

const SetupFrame = () => (
  <div>
    <h2 id="setup">Setup</h2>
    <form className="form-horizontal" role="form">
      <EventSelectorContainer />
      <AuthToolsContainer />
      <AuthInputContainer />
    </form>
  </div>
)

export default SetupFrame
