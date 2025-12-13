import { connect, ConnectedProps } from "react-redux";
import { Dispatch } from "redux";
import AuthTools from "../components/AuthTools";
import { updateAuth, AuthAction } from "../actions";
import { RootState } from "../reducers";

const mapStateToProps = (state: RootState) => ({
  authId: state.auth.authId,
  authSecret: state.auth.authSecret,
  manualEvent: state.auth.manualEvent,
  selectedEvent: state.auth.selectedEvent,
});

const mapDispatchToProps = (dispatch: Dispatch<AuthAction>) => ({
  setAuth: (authId: string, authSecret: string) =>
    dispatch(updateAuth(authId, authSecret)),
});

const connector = connect(mapStateToProps, mapDispatchToProps);

export type AuthToolsContainerProps = ConnectedProps<typeof connector>;

export default connector(AuthTools);
