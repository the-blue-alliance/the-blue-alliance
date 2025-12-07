import React, { ChangeEvent } from "react";

interface AuthInputProps {
  authId?: string;
  authSecret?: string;
  manualEvent?: boolean;
  setAuth: (authId: string, authSecret: string) => void;
}

const AuthInput: React.FC<AuthInputProps> = ({
  authId,
  authSecret,
  manualEvent,
  setAuth,
}) => {
  const handleAuthIdChange = (event: ChangeEvent<HTMLInputElement>): void => {
    setAuth(event.target.value, authSecret || "");
  };

  const handleAuthSecretChange = (event: ChangeEvent<HTMLInputElement>): void => {
    setAuth(authId || "", event.target.value);
  };

  if (!manualEvent) {
    return null;
  }

  return (
    <div id="auth-container">
      <div className="form-group">
        <label htmlFor="auth_id" className="col-sm-2 control-label">
          Auth Id
        </label>
        <div className="col-sm-10">
          <input
            type="password"
            className="form-control"
            id="auth_id"
            placeholder="Auth ID"
            value={authId || ""}
            onChange={handleAuthIdChange}
          />
        </div>
      </div>
      <div className="form-group">
        <label htmlFor="auth_secret" className="col-sm-2 control-label">
          Auth Secret
        </label>
        <div className="col-sm-10">
          <input
            type="password"
            className="form-control"
            id="auth_secret"
            placeholder="Auth Secret"
            value={authSecret || ""}
            onChange={handleAuthSecretChange}
          />
        </div>
      </div>
    </div>
  );
};

export default AuthInput;
