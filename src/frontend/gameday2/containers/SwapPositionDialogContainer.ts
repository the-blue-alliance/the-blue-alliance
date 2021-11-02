import { connect } from "react-redux";
import SwapPositionDialog from "../components/SwapPositionDialog";
import { swapWebcasts } from "../actions";

const mapStateToProps = (state: any) => ({
  layoutId: state.videoGrid.layoutId,
});

const mapDispatchToProps = (dispatch: any) => ({
  swapWebcasts: (firstPosition: any, secondPosition: any) =>
    dispatch(swapWebcasts(firstPosition, secondPosition)),
});

export default connect(mapStateToProps, mapDispatchToProps)(SwapPositionDialog);
