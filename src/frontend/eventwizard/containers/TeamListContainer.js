import { connect } from "react-redux";
import TeamListTab from "../components/teamsTab/TeamListTab";
import makeTrustedApiRequest from "../net/TrustedApiRequest";

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
});

export default connect(mapStateToProps)(TeamListTab);
