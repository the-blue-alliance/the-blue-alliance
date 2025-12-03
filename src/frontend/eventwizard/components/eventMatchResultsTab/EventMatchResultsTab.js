import React from "react";
import PropTypes from "prop-types";
import FMSMatchResults from "./FMSMatchResults";
import MatchResultsFromMatchPlay from "./MatchResultsFromMatchPlay";

function EventMatchResultsTab({
  selectedEvent,
  makeTrustedRequest,
  makeApiV3Request,
}) {
  return (
    <div className="tab-pane" id="matches">
      <h3>Match Results</h3>

      <FMSMatchResults
        selectedEvent={selectedEvent}
        makeTrustedRequest={makeTrustedRequest}
      />

      <hr style={{ margin: "40px 0" }} />

      <MatchResultsFromMatchPlay
        selectedEvent={selectedEvent}
        makeTrustedRequest={makeTrustedRequest}
        makeApiV3Request={makeApiV3Request}
      />
    </div>
  );
}

EventMatchResultsTab.propTypes = {
  selectedEvent: PropTypes.string.isRequired,
  makeTrustedRequest: PropTypes.func.isRequired,
  makeApiV3Request: PropTypes.func.isRequired,
};

export default EventMatchResultsTab;
