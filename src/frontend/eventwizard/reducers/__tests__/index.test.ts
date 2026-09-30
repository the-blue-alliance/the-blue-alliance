import eventwizardReducer from "../index";
import { setEvent, setManualEvent, updateAuth, clearAuth } from "../../actions";

describe("eventwizardReducer", () => {
  it("initialises with the auth slice's default state", () => {
    const state = eventwizardReducer(undefined, { type: "@@INIT" } as any);
    expect(state).toEqual({
      auth: { selectedEvent: "", manualEvent: false },
    });
  });

  it("routes auth actions to the auth slice", () => {
    let state = eventwizardReducer(undefined, setEvent("2025nysu"));
    state = eventwizardReducer(state, setManualEvent(true));
    state = eventwizardReducer(state, updateAuth("id", "secret"));
    expect(state.auth).toEqual({
      selectedEvent: "2025nysu",
      manualEvent: true,
      authId: "id",
      authSecret: "secret",
    });

    state = eventwizardReducer(state, clearAuth());
    expect(state.auth.authId).toBe("");
    expect(state.auth.authSecret).toBe("");
  });
});
