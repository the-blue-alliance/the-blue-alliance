import { connect } from "react-redux";
import MatchVideosTab from "../components/matchVideosTab/MatchVideosTab";
import makeTrustedApiRequest from "../net/TrustedApiRequest";
import makeApiV3Request from "../net/ApiV3Request";
import { RootState } from "../reducers";

const mapStateToProps = (state: RootState) => ({
  selectedEvent: state.auth.selectedEvent,
  makeTrustedRequest: (
    requestPath: string,
    requestBody: string
  ) => {
    return makeTrustedApiRequest(
      state.auth.authId || "",
      state.auth.authSecret || "",
      requestPath,
      requestBody
    );
  },
  makeApiV3Request: (
    requestPath: string
  ) => {
    return makeApiV3Request(state.auth.authId || "", requestPath);
  },
});

const connector = connect(mapStateToProps);

export default connector(MatchVideosTab);
