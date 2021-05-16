import { connect } from "react-redux";
import VideoCell from "../components/VideoCell";
import {
  addWebcastAtPosition,
  setLayout,
  swapWebcasts,
  togglePositionLivescore,
} from "../actions";
import { getWebcastIdsInDisplayOrder } from "../selectors";

const mapStateToProps = (state: any) => ({
  webcasts: getWebcastIdsInDisplayOrder(state),
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
});

const mapDispatchToProps = (dispatch: any) => ({
  addWebcastAtPosition: (webcastId: any, position: any) =>
    dispatch(addWebcastAtPosition(webcastId, position)),

  setLayout: (layoutId: any) => dispatch(setLayout(layoutId)),

  swapWebcasts: (firstPosition: any, secondPosition: any) =>
    dispatch(swapWebcasts(firstPosition, secondPosition)),

  togglePositionLivescore: (position: any) =>
    dispatch(togglePositionLivescore(position)),
});

export default connect(mapStateToProps, mapDispatchToProps)(VideoCell);
