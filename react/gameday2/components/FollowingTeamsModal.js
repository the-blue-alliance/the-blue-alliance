import React, { PropTypes } from 'react'
import FollowingTeamListItem from './FollowingTeamListItem'

const FollowingTeamsModal = React.createClass({
  propTypes: {
    onFollowTeam: PropTypes.func,
    onUnfollowTeam: PropTypes.func,
    followingTeams: PropTypes.array,
  },
  followTeam() {
    this.props.onFollowTeam(177)
  },
  render() {
    const followingTeamListItems = []
    Object.keys(this.props.followingTeams).forEach((team) => {
      followingTeamListItems.push(
        <FollowingTeamListItem
          key={this.props.followingTeams[team]}
          team={this.props.followingTeams[team]}
          onUnfollowTeam={this.props.onUnfollowTeam}
        />
      )
    })
    return (
      <div className="modal fade" id="followingTeamsModal" tabIndex="-1" role="dialog" aria-labelledby="#followingTeamsModal" aria-hidden="true">
        <div className="modal-dialog">
          <div className="modal-content">
            <div className="modal-header">
              <button type="button" className="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span className="sr-only">Close</span></button>
              <h4 className="modal-title" id="followingTeamsModalLabel">Following Teams</h4>
            </div>
            <div className="modal-body">
              <p>You can follow teams to get alerts about them.</p>
              <div className="input-group">
                <input className="form-control" type="text" placeholder="Team Number" />
                <span className="input-group-btn">
                  <a onClick={this.followTeam} href="#" className="btn btn-primary"><span className="glyphicon glyphicon-plus-sign" /></a>
                </span>
              </div>
              <hr />
              <h4>Following</h4>
              <ul>{followingTeamListItems}</ul>
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-primary" data-dismiss="modal">Done</button>
            </div>
          </div>
        </div>
      </div>
    )
  },
})

export default FollowingTeamsModal
