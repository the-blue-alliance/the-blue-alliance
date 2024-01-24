import { connect } from "react-redux";
import AwardsTab from "../components/awardsTab/AwardsTab";
import makeTrustedApiRequest from "../net/TrustedApiRequest";

const mapStateToProps = (state) => ({
  selectedEvent: state.auth.selectedEvent,
  makeTrustedRequest: (requestPath, requestBody, onSuccess, onError) => {
    makeTrustedApiRequest(
      state.authId,
      state.authSecret,
      requestPath,
      requestBody,
      onSuccess,
      onError
    );
  },
});

export default connect(mapStateToProps)(AwardsTab);
