import React from "react";
import Button from "@mui/material/Button";

export default () => (
  <div className="no-webcasts-container">
    <h1>No webcasts found</h1>
    <p>
      Looks like there aren&apos;t any events with webcasts this week. Check on
      The Blue Alliance for upcoming events!
    </p>
    <Button
      variant="contained"
      href="https://www.thebluealliance.com"
      label="Go to The Blue Alliance"
    />
  </div>
);
