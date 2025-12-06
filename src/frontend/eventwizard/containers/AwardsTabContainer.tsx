import { connect } from "react-redux";
import AwardsTab from "../components/awardsTab/AwardsTab";
import makeTrustedApiRequest from "../net/TrustedApiRequest";
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
});

const connector = connect(mapStateToProps);

export default connector(AwardsTab);
