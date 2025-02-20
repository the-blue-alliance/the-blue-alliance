import React, { Component } from "react";
import PropTypes from "prop-types";

class AuthTools extends Component {
  constructor(props) {
    super(props);
    this.storeAuth = this.storeAuth.bind(this);
    this.loadAuth = this.loadAuth.bind(this);
  }

  storeAuth() {
    if (!this.props.selectedEvent) {
      alert("You must enter an event key");
      return;
    }

    if (!this.props.authId || !this.props.authSecret) {
      alert("You must enter you auth ID and secret");
      return;
    }

    const auth = {};
    auth.id = this.props.authId;
    auth.secret = this.props.authSecret;

    localStorage.setItem(
      `${this.props.selectedEvent}_auth`,
      JSON.stringify(auth)
    );
    alert("Auth Stored");
  }

  loadAuth() {
    if (!this.props.selectedEvent) {
      alert("You must select an event");
      return;
    }

    const auth = localStorage.getItem(`${this.props.selectedEvent}_auth`);
    if (!auth) {
      alert(`No auth found for ${this.props.selectedEvent}`);
      return;
    }

    const authData = JSON.parse(auth);
    this.props.setAuth(authData.id, authData.secret);
    alert("Auth Loaded");
  }

  render() {
    if (!this.props.manualEvent) {
      return null;
    }

    return (
      <div className="form-group" id="auth-tools">
        <label className="col-sm-2 control-label" htmlFor="load_auth">
          Auth Tools
        </label>
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
    );
  }
}

AuthTools.propTypes = {
  authId: PropTypes.string,
  authSecret: PropTypes.string,
  manualEvent: PropTypes.bool,
  selectedEvent: PropTypes.string,
  setAuth: PropTypes.func.isRequired,
};

export default AuthTools;
