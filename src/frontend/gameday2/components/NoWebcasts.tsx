import React from "react";
// @ts-expect-error ts-migrate(7016) FIXME: Could not find a declaration file for module 'mate... Remove this comment to see the full error message
import RaisedButton from "material-ui/RaisedButton";

export default () => (
  <div className="no-webcasts-container">
    <h1>No webcasts found</h1>
    <p>
      Looks like there aren&apos;t any events with webcasts this week. Check on
      The Blue Alliance for upcoming events!
    </p>
    <RaisedButton
      href="https://www.thebluealliance.com"
      label="Go to The Blue Alliance"
    />
  </div>
);
