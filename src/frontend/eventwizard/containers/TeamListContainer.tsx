import { connect } from "react-redux";
import TeamListTab from "../components/teamsTab/TeamListTab";
import makeTrustedApiRequest from "../net/TrustedApiRequest";
import { RootState } from "../reducers";
import makeApiV3Request from "../net/ApiV3Request";

const mapStateToProps = (state: RootState) => ({
  selectedEvent: state.auth.selectedEvent,
  makeTrustedRequest: (
    requestPath: string,
    requestBody: string | FormData
  ) => {
    return makeTrustedApiRequest(
      state.auth.authId || "",
      state.auth.authSecret || "",
      requestPath,
      requestBody
    );
  },
  makeApiV3Request: (
    requestPath: string,
  ) => {
    return makeApiV3Request(
      state.auth.authId || "",
      requestPath,
    );
  },
});

const connector = connect(mapStateToProps);

export default connector(TeamListTab);
