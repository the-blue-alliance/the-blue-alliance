import React, { PropTypes } from 'react'

export default React.createClass({
  propTypes: {
    team: PropTypes.string,
    onUnfollowTeam: PropTypes.func,
  },
  unfollowTeam() {
    this.props.onUnfollowTeam(this.props.team)
  },
  render() {
    return (
      <li>
        {this.props.team}
        <a href="#" onClick={this.unfollowTeam}>&times;</a>
      </li>
    )
  },
})
