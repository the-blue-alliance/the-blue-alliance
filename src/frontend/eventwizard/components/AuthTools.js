import React, { Component } from "react";
import PropTypes from "prop-types";
import Alert from "@mui/material/Alert";

class AuthTools extends Component {
  constructor(props) {
    super(props);
    this.state = {
      alert: null,
    };
    this.storeAuth = this.storeAuth.bind(this);
    this.loadAuth = this.loadAuth.bind(this);
    this.clearAlert = this.clearAlert.bind(this);
  }

  clearAlert() {
    this.setState({ alert: null });
  }

  storeAuth() {
    if (!this.props.selectedEvent) {
      this.setState({
        alert: { severity: "error", message: "You must enter an event key" },
      });
      return;
    }

    if (!this.props.authId || !this.props.authSecret) {
      this.setState({
        alert: {
          severity: "error",
          message: "You must enter you auth ID and secret",
        },
      });
      return;
    }

    const auth = {};
    auth.id = this.props.authId;
    auth.secret = this.props.authSecret;

    localStorage.setItem(
      `${this.props.selectedEvent}_auth`,
      JSON.stringify(auth)
    );
    this.setState({ alert: { severity: "success", message: "Auth Stored" } });
  }

  loadAuth() {
    if (!this.props.selectedEvent) {
      this.setState({
        alert: { severity: "error", message: "You must select an event" },
      });
      return;
    }

    const auth = localStorage.getItem(`${this.props.selectedEvent}_auth`);
    if (!auth) {
      this.setState({
        alert: {
          severity: "error",
          message: `No auth found for ${this.props.selectedEvent}`,
        },
      });
      return;
    }

    const authData = JSON.parse(auth);
    this.props.setAuth(authData.id, authData.secret);
    this.setState({ alert: { severity: "success", message: "Auth Loaded" } });
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
          {this.state.alert && (
            <Alert
              severity={this.state.alert.severity}
              icon={false}
              onClose={this.clearAlert}
              sx={{ mb: 2, fontSize: 14 }}
            >
              {this.state.alert.message}
            </Alert>
          )}
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
