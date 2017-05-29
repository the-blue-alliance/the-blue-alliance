import React, { Component } from 'react'
import PropTypes from 'prop-types'
import Dialog from 'react-bootstrap-dialog'

class AuthTools extends Component {

  constructor(props) {
    super(props)
    this.storeAuth = this.storeAuth.bind(this)
    this.loadAuth = this.loadAuth.bind(this)
  }

  storeAuth() {
    if (!this.props.selectedEvent) {
      this.refs.dialog.show({
        title: 'Error',
        body: 'You must enter an event key',
        actions: [
          Dialog.OKAction()
        ],
      })
      return
    }

    if (!this.props.authId || !this.props.authSecret) {
      this.refs.dialog.show({
        title: 'Error',
        body: 'You must enter you auth ID and secret',
        actions: [
          Dialog.OKAction()
        ],
      })
      return
    }

    const auth = {}
    auth.id = this.props.authId
    auth.secret = this.props.authSecret

    localStorage.setItem(`${this.props.selectedEvent}_auth`, JSON.stringify(auth))
    this.refs.dialog.show({
      title: 'Success',
      body: 'Auth Stored',
      actions: [
        Dialog.OKAction()
      ],
    })
  }

  loadAuth() {
    if (!this.props.selectedEvent) {
      this.refs.dialog.show({
        title: 'Error',
        body: 'You must select an event',
        actions: [
          Dialog.OKAction()
        ],
      })
      return
    }

    const auth = localStorage.getItem(`${this.props.selectedEvent}_auth`)
    if (!auth) {
      this.refs.dialog.show({
        title: 'Error',
        body: `No auth found for ${this.props.selectedEvent}`,
        actions: [
          Dialog.OKAction()
        ],
      })
      return
    }

    const authData = JSON.parse(auth)
    this.props.setAuth(authData.id, authData.secret)
    this.refs.dialog.show({
      title: 'Success',
      body: 'Auth Loaded',
      actions: [
        Dialog.OKAction()
      ],
    })
  }

  render() {
    if (!this.props.manualEvent) {
      return null
    }

    return (
      <div className="form-group" id="auth-tools">
        <Dialog ref="dialog" />
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
