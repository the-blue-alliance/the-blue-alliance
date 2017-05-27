import React, { Component } from 'react'
import PropTypes from 'prop-types'

class AuthTools extends Component {

  constructor(props) {
    super(props)
    this.state = {
      errorMessage: null,
      successMessage: null,
    }
    this.storeAuth = this.storeAuth.bind(this)
    this.loadAuth = this.loadAuth.bind(this)
  }

  storeAuth() {
    if (!this.props.selectedEvent) {
      this.setState({
        successMessage: null,
        errorMessage: 'You must enter an event key.',
      })
      return
    }

    if (!this.props.authId || !this.props.authSecret) {
      this.setState({
        successMessage: null,
        errorMessage: 'You must enter your auth id and secret.',
      })
      return
    }

    const auth = {}
    auth.id = this.props.authId
    auth.secret = this.props.authSecret

    localStorage.setItem(`${this.props.selectedEvent}_auth`, JSON.stringify(auth))
    this.setState({
      errorMessage: null,
      successMessage: 'Auth Stored!',
    })
  }

  loadAuth() {
    if (!this.props.selectedEvent) {
      this.setState({
        successMessage: null,
        errorMessage: 'You must enter an event key.',
      })
      return
    }

    const auth = localStorage.getItem(`${this.props.selectedEvent}_auth`)
    if (!auth) {
      this.setState({
        successMessage: null,
        errorMessage: `No auth found for ${this.props.selectedEvent}`,
      })
      return
    }

    const authData = JSON.parse(auth)
    this.props.setAuth(authData.id, authData.secret)
    this.setState({
      errorMessage: null,
      successMessage: 'Auth Loaded!',
    })
  }

  render() {
    if (!this.props.manualEvent) {
      return null
    }

    return (

      <div className="form-group" id="auth-tools">
        <div
          className="alert alert-danger"
          style={{ display: this.state.errorMessage ? 'block' : 'none' }}
        >
          <button type="button" className="close" data-dismiss="alert">&times;</button>
          <p><strong>Error!</strong> {this.state.errorMessage}</p>
        </div>
        <div
          className="alert alert-success"
          style={{ display: this.state.successMessage ? 'block' : 'none' }}
        >
          <button type="button" className="close" data-dismiss="alert">&times;</button>
          <p>{this.state.successMessage}</p>
        </div>
        <label className="col-sm-2 control-label" htmlFor="load_auth">Auth Tools</label>
        <div className="col-sm-10">
          <button
            type="button"
            className="btn btn-default"
            id="load_auth"
            onClick={this.loadAuth}
          >
            Load Auth
          </button>
          <button
            type="button"
            className="btn btn-default"
            id="store_auth"
            onClick={this.storeAuth}
          >
            Store Auth
          </button>
        </div>
      </div>
    )
  }
}

AuthTools.propTypes = {
  authId: PropTypes.string,
  authSecret: PropTypes.string,
  manualEvent: PropTypes.bool,
  selectedEvent: PropTypes.string,
  setAuth: PropTypes.func.isRequired,
}

export default AuthTools
