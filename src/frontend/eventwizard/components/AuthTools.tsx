import React, { Component } from "react";
import Alert from "@mui/material/Alert";

interface AuthData {
  id: string;
  secret: string;
}

interface AlertState {
  severity: "success" | "error";
  message: string;
}

interface AuthToolsProps {
  authId?: string;
  authSecret?: string;
  manualEvent?: boolean;
  selectedEvent?: string;
  setAuth: (authId: string, authSecret: string) => void;
}

interface AuthToolsState {
  alert: AlertState | null;
}

class AuthTools extends Component<AuthToolsProps, AuthToolsState> {
  constructor(props: AuthToolsProps) {
    super(props);
    this.state = {
      alert: null,
    };
    this.storeAuth = this.storeAuth.bind(this);
    this.loadAuth = this.loadAuth.bind(this);
    this.clearAlert = this.clearAlert.bind(this);
  }

  clearAlert(): void {
    this.setState({ alert: null });
  }

  storeAuth(): void {
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

    const auth: AuthData = {
      id: this.props.authId,
      secret: this.props.authSecret,
    };

    localStorage.setItem(
      `${this.props.selectedEvent}_auth`,
      JSON.stringify(auth)
    );
    this.setState({ alert: { severity: "success", message: "Auth Stored" } });
  }

  loadAuth(): void {
    if (!this.props.selectedEvent) {
      this.setState({
        alert: { severity: "error", message: "You must select an event" },
      });
      return;
    }

    const authString = localStorage.getItem(`${this.props.selectedEvent}_auth`);
    if (!authString) {
      this.setState({
        alert: {
          severity: "error",
          message: `No auth found for ${this.props.selectedEvent}`,
        },
      });
      return;
    }

    const authData: AuthData = JSON.parse(authString);
    this.props.setAuth(authData.id, authData.secret);
    this.setState({ alert: { severity: "success", message: "Auth Loaded" } });
  }

  render(): React.ReactNode {
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

export default AuthTools;
