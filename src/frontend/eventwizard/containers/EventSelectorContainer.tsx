import { connect, ConnectedProps } from "react-redux";
import { Dispatch } from "redux";
import EventSelector from "../components/EventSelector";
import { setEvent, setManualEvent, clearAuth, AuthAction } from "../actions";
import { RootState } from "../reducers";

const mapStateToProps = (state: RootState) => ({
  selectedEvent: state.auth.selectedEvent,
  manualEvent: state.auth.manualEvent,
});

const mapDispatchToProps = (dispatch: Dispatch<AuthAction>) => ({
  setEvent: (eventKey: string) => dispatch(setEvent(eventKey)),
  setManualEvent: (manualEvent: boolean) => dispatch(setManualEvent(manualEvent)),
  clearAuth: () => dispatch(clearAuth()),
});

const connector = connect(mapStateToProps, mapDispatchToProps);

export type EventSelectorContainerProps = ConnectedProps<typeof connector>;

export default connector(EventSelector);
