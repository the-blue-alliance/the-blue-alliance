import { connect } from "react-redux";
import AwardsTab from "../components/awardsTab/AwardsTab";
import makeTrustedApiRequest from "../net/TrustedApiRequest";
import { RootState } from "../reducers";

const mapStateToProps = (state: RootState) => ({
  selectedEvent: state.auth.selectedEvent,
  makeTrustedRequest: (
    requestPath: string,
    requestBody: string,
    onSuccess: (response: Response) => void,
    onError: (error: Error) => void
  ) => {
    makeTrustedApiRequest(
      state.auth.authId || "",
      state.auth.authSecret || "",
      requestPath,
      requestBody,
      onSuccess,
      onError
    );
  },
});

const connector = connect(mapStateToProps);

export default connector(AwardsTab);
