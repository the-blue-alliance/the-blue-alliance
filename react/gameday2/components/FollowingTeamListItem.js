import React from 'react'

export default React.createClass({
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
