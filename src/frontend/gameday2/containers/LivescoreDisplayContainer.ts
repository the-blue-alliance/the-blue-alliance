import { connect } from "react-redux";
import LivescoreDisplay from "../components/LivescoreDisplay";
import { getEventMatches, getCurrentMatchState } from "../selectors";

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'state' implicitly has an 'any' type.
const mapStateToProps = (state, props) => ({
  matches: getEventMatches(state, props),
  matchState: getCurrentMatchState(state, props),
});

export default connect(mapStateToProps)(LivescoreDisplay);
