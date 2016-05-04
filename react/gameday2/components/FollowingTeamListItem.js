import React from 'react';

var FollowingTeamListItem = React.createClass({
  unfollowTeam: function() {
    this.props.onUnfollowTeam(this.props.team)
  },
  render: function() {
    return (
      <li>
        {this.props.team}
        <a href="#" onClick={this.unfollowTeam}>&times;</a>
      </li>
    );
  }
});

export default FollowingTeamListItem;
