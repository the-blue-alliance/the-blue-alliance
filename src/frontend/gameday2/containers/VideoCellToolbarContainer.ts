import { connect } from "react-redux";
import VideoCellToolbar from "../components/VideoCellToolbar";
import { addWebcastAtPosition, swapWebcasts, removeWebcast } from "../actions";
import { getTickerMatches, getWebcastIdsInDisplayOrder } from "../selectors";

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'state' implicitly has an 'any' type.
const mapStateToProps = (state, props) => ({
  matches: getTickerMatches(state, props),
  favoriteTeams: state.favoriteTeams,
  webcasts: getWebcastIdsInDisplayOrder(state),
  webcastsById: state.webcastsById,
  specialWebcastIds: state.specialWebcastIds,
  displayedWebcasts: state.videoGrid.displayed,
  layoutId: state.videoGrid.layoutId,
});

const mapDispatchToProps = (dispatch: any) => ({
  removeWebcast: (id: any) => dispatch(removeWebcast(id)),

  addWebcastAtPosition: (webcastId: any, position: any) =>
    dispatch(addWebcastAtPosition(webcastId, position)),

  swapWebcasts: (firstPosition: any, secondPosition: any) =>
    dispatch(swapWebcasts(firstPosition, secondPosition)),
});

export default connect(mapStateToProps, mapDispatchToProps)(VideoCellToolbar);
