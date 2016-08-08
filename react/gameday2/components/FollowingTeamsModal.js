import React from 'react'
import FollowingTeamListItem from './FollowingTeamListItem'

const FollowingTeamsModal = React.createClass({
  followTeam() {
    this.props.onFollowTeam(177)
  },
  render() {
    let followingTeamListItems = []
    for (const index in this.props.followingTeams) {
      followingTeamListItems.push(
        <FollowingTeamListItem
          key={this.props.followingTeams[index]}
          team={this.props.followingTeams[index]}
          onUnfollowTeam={this.props.onUnfollowTeam}
        />
      )
    }
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
                <input className="form-control" type="text" placeholder="Team Number"></input>
                <span className="input-group-btn">
                  <a onClick={this.followTeam} href="#" className="btn btn-primary"><span className="glyphicon glyphicon-plus-sign"></span></a>
                </span>
              </div>
              <hr></hr>
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
