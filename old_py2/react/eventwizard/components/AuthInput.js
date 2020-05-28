import React, { Component } from 'react'
import PropTypes from 'prop-types'

class AuthInput extends Component {
  constructor(props) {
    super(props)
    this.onAuthIdChange = this.onAuthIdChange.bind(this)
    this.onAuthSecretChange = this.onAuthSecretChange.bind(this)
  }

  onAuthIdChange(event) {
    this.props.setAuth(event.target.value, this.props.authSecret)
  }

  onAuthSecretChange(event) {
    this.props.setAuth(this.props.authId, event.target.value)
  }

  render() {
    if (!this.props.manualEvent) {
      return null
    }

    return (
      <div id="auth-container">
        <div className="form-group">
          <label htmlFor="auth_id" className="col-sm-2 control-label">Auth Id</label>
          <div className="col-sm-10">
            <input
              type="password"
              className="form-control"
              id="auth_id"
              placeholder="Auth ID"
              value={this.props.authId}
              onChange={this.onAuthIdChange}
            />
          </div>
        </div>
        <div className="form-group">
          <label htmlFor="auth_secret" className="col-sm-2 control-label">Auth Secret</label>
          <div className="col-sm-10">
            <input
              type="password"
              className="form-control"
              id="auth_secret"
              placeholder="Auth Secret"
              value={this.props.authSecret}
              onChange={this.onAuthSecretChange}
            />
          </div>
        </div>
      </div>
    )
  }
}

AuthInput.propTypes = {
  authId: PropTypes.string,
  authSecret: PropTypes.string,
  manualEvent: PropTypes.bool,
  setAuth: PropTypes.func.isRequired,
}

export default AuthInput
