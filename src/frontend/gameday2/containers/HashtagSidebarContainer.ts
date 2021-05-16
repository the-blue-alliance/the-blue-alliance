import { connect } from "react-redux";
import HashtagSidebar from "../components/HashtagSidebar";

const mapStateToProps = (state: any) => ({
  enabled: state.visibility.hashtagSidebar,
});

export default connect(mapStateToProps, null)(HashtagSidebar);
