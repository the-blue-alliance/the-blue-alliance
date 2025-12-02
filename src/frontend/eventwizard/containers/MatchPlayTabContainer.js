import { connect } from "react-redux";
import MatchPlayTab from "../components/matchPlayTab/MatchPlayTab";
import makeTrustedApiRequest from "../net/TrustedApiRequest";
import makeApiV3Request from "../net/ApiV3Request";

const mapStateToProps = (state) => ({
  selectedEvent: state.auth.selectedEvent,
  makeTrustedRequest: (requestPath, requestBody, onSuccess, onError) => {
    makeTrustedApiRequest(
      state.auth.authId,
      state.auth.authSecret,
      requestPath,
      requestBody,
      onSuccess,
      onError
    );
  },
  makeApiV3Request: (requestPath, onSuccess, onError) => {
    makeApiV3Request(state.auth.authId, requestPath, onSuccess, onError);
  },
});

export default connect(mapStateToProps)(MatchPlayTab);
