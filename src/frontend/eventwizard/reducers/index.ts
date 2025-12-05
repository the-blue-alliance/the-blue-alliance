import { combineReducers } from "redux";
import auth, { AuthState } from "./auth";

export interface RootState {
  auth: AuthState;
}

const eventwizardReducer = combineReducers({
  auth,
});

export default eventwizardReducer;

export type AppState = ReturnType<typeof eventwizardReducer>;
