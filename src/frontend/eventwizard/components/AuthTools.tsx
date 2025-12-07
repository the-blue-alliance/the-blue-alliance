import React, { useState } from "react";
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

const AuthTools: React.FC<AuthToolsProps> = ({
  authId,
  authSecret,
  manualEvent,
  selectedEvent,
  setAuth,
}) => {
  const [alert, setAlert] = useState<AlertState | null>(null);

  const handleClearAlert = (): void => {
    setAlert(null);
  };

  const handleStoreAuth = (): void => {
    if (!selectedEvent) {
      setAlert({ severity: "error", message: "You must enter an event key" });
      return;
    }

    if (!authId || !authSecret) {
      setAlert({
        severity: "error",
        message: "You must enter you auth ID and secret",
      });
      return;
    }

    const auth: AuthData = {
      id: authId,
      secret: authSecret,
    };

    localStorage.setItem(
      `${selectedEvent}_auth`,
      JSON.stringify(auth)
    );
    setAlert({ severity: "success", message: "Auth Stored" });
  };

  const handleLoadAuth = (): void => {
    if (!selectedEvent) {
      setAlert({ severity: "error", message: "You must select an event" });
      return;
    }

    const authString = localStorage.getItem(`${selectedEvent}_auth`);
    if (!authString) {
      setAlert({
        severity: "error",
        message: `No auth found for ${selectedEvent}`,
      });
      return;
    }

    const authData: AuthData = JSON.parse(authString);
    setAuth(authData.id, authData.secret);
    setAlert({ severity: "success", message: "Auth Loaded" });
  };

  if (!manualEvent) {
    return null;
  }

  return (
    <div className="form-group" id="auth-tools">
      <label className="col-sm-2 control-label" htmlFor="load_auth">
        Auth Tools
      </label>
      <div className="col-sm-10">
        {alert && (
          <Alert
            severity={alert.severity}
            icon={false}
            onClose={handleClearAlert}
            sx={{ mb: 2, fontSize: 14 }}
          >
            {alert.message}
          </Alert>
        )}
        <button
          type="button"
          className="btn btn-default"
          id="load_auth"
          onClick={handleLoadAuth}
        >
          Load Auth
        </button>
        <button
          type="button"
          className="btn btn-default"
          id="store_auth"
          onClick={handleStoreAuth}
        >
          Store Auth
        </button>
      </div>
    </div>
  );
};

export default AuthTools;
