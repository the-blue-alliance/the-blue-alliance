import { connect } from "react-redux";
import EventInfoTab from "../components/infoTab/EventInfoTab";
import makeTrustedApiRequest from "../net/TrustedApiRequest";
import makeApiV3Request from "../net/ApiV3Request";
import { RootState } from "../reducers";

const mapStateToProps = (state: RootState) => ({
  authId: state.auth.authId,
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

export default connector(EventInfoTab);
