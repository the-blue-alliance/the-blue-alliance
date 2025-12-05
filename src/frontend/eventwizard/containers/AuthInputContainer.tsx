import { connect, ConnectedProps } from "react-redux";
import { Dispatch } from "redux";
import AuthInput from "../components/AuthInput";
import { updateAuth, AuthAction } from "../actions";
import { RootState } from "../reducers";

const mapStateToProps = (state: RootState) => ({
  authId: state.auth.authId,
  authSecret: state.auth.authSecret,
  selectedEvent: state.auth.selectedEvent,
  manualEvent: state.auth.manualEvent,
});

const mapDispatchToProps = (dispatch: Dispatch<AuthAction>) => ({
  setAuth: (authId: string, authSecret: string) =>
    dispatch(updateAuth(authId, authSecret)),
});

const connector = connect(mapStateToProps, mapDispatchToProps);

export type AuthInputContainerProps = ConnectedProps<typeof connector>;

export default connector(AuthInput);
