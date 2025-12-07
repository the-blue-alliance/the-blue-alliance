import { connect } from "react-redux";
import EventInfoTab from "../components/infoTab/EventInfoTab";
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
  makeApiV3Request: <T = unknown>(
    requestPath: string
  ) => {
    return makeApiV3Request<T>(state.auth.authId || "", requestPath);
  },
});

const connector = connect(mapStateToProps);

export default connector(EventInfoTab);
