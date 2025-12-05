import { connect } from "react-redux";
import MatchVideosTab from "../components/matchVideosTab/MatchVideosTab";
import makeTrustedApiRequest from "../net/TrustedApiRequest";
import makeApiV3Request from "../net/ApiV3Request";
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
  makeApiV3Request: <T = unknown>(
    requestPath: string,
    onSuccess: (data: T) => void,
    onError: (error: string) => void
  ) => {
    makeApiV3Request(state.auth.authId || "", requestPath, onSuccess, onError);
  },
});

const connector = connect(mapStateToProps);

export default connector(MatchVideosTab);
