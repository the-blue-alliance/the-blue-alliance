import React from 'react'
import EventWizardTabFrame from './EventWizardTabFrame'
import SetupFrame from './SetupFrame'

const EventWizardFrame = () => (
  <div className="container">
    <div className="row">
      <div className="col-xs-12">
        <h1 className="endheader">TBA Event Wizard</h1>
        <p>A tool to input FRC event data. <a href="/add-data">Visit this page</a> for more info if you are running an offseason event and would like to import your data to TBA, or <a href="/contact">contact us</a>.</p>
        <p>For help using this tool, please refer to the <a href="https://docs.google.com/document/d/1RWcsehMDXzlAyv4p5srwofknYvdNt6noejpMSYZMmeA/pub">User Guide</a>.</p>
        <hr />
        <SetupFrame />
        <EventWizardTabFrame />
      </div>
    </div>
  </div>
)

export default EventWizardFrame
