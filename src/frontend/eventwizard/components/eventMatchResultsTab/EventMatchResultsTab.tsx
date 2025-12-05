import React from "react";
import FMSMatchResults from "./FMSMatchResults";
import MatchResultsFromMatchPlay from "./MatchResultsFromMatchPlay";

interface EventMatchResultsTabProps {
  selectedEvent: string;
  makeTrustedRequest: (
    path: string,
    body: string,
    successCallback: (response: any) => void,
    errorCallback: (error: any) => void
  ) => void;
  makeApiV3Request: (
    path: string,
    successCallback: (response: any) => void,
    errorCallback: (error: any) => void
  ) => void;
}

const EventMatchResultsTab: React.FC<EventMatchResultsTabProps> = ({
  selectedEvent,
  makeTrustedRequest,
  makeApiV3Request,
}) => {
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
};

export default EventMatchResultsTab;
