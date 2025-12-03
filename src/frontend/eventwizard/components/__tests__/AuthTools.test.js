import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import AuthTools from "../AuthTools";

describe("AuthTools", () => {
  const mockSetAuth = jest.fn();
  let mockLocalStorage;

  beforeEach(() => {
    mockLocalStorage = {
      getItem: jest.fn(),
      setItem: jest.fn(),
    };
    global.localStorage = mockLocalStorage;
  });

  afterEach(() => {
    jest.clearAllMocks();
    delete global.localStorage;
  });

  it("renders nothing when manualEvent is false", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId=""
        authSecret=""
        manualEvent={false}
        selectedEvent=""
        setAuth={mockSetAuth}
      />
    );
    expect(html).toBe("");
  });

  it("renders auth tools when manualEvent is true", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId="test_id"
        authSecret="test_secret"
        manualEvent={true}
        selectedEvent="2024test"
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain('id="auth-tools"');
    expect(html).toContain("Auth Tools");
  });

  it("renders Load Auth button", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId=""
        authSecret=""
        manualEvent={true}
        selectedEvent="2024test"
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain('id="load_auth"');
    expect(html).toContain("Load Auth");
  });

  it("renders Store Auth button", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId=""
        authSecret=""
        manualEvent={true}
        selectedEvent="2024test"
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain('id="store_auth"');
    expect(html).toContain("Store Auth");
  });

  it("renders buttons with correct classes", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId=""
        authSecret=""
        manualEvent={true}
        selectedEvent="2024test"
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain('class="btn btn-default"');
  });

  it("renders form-group with proper structure", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId=""
        authSecret=""
        manualEvent={true}
        selectedEvent="2024test"
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain("form-group");
    expect(html).toContain("control-label");
    expect(html).toContain("col-sm-2");
    expect(html).toContain("col-sm-10");
  });

  it("stores auth in localStorage when storeAuth is called", () => {
    const component = new AuthTools({
      authId: "test_id",
      authSecret: "test_secret",
      manualEvent: true,
      selectedEvent: "2024test",
      setAuth: mockSetAuth,
    });
    // Mock setState to capture the state change
    component.setState = jest.fn((newState) => {
      component.state = { ...component.state, ...newState };
    });
    component.storeAuth();
    expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
      "2024test_auth",
      JSON.stringify({ id: "test_id", secret: "test_secret" })
    );
    expect(component.setState).toHaveBeenCalledWith({
      alert: { severity: "success", message: "Auth Stored" },
    });
  });

  it("loads auth from localStorage when loadAuth is called", () => {
    mockLocalStorage.getItem.mockReturnValue(
      JSON.stringify({ id: "stored_id", secret: "stored_secret" })
    );
    const component = new AuthTools({
      authId: "",
      authSecret: "",
      manualEvent: true,
      selectedEvent: "2024test",
      setAuth: mockSetAuth,
    });
    // Mock setState to capture the state change
    component.setState = jest.fn((newState) => {
      component.state = { ...component.state, ...newState };
    });
    component.loadAuth();
    expect(mockLocalStorage.getItem).toHaveBeenCalledWith("2024test_auth");
    expect(mockSetAuth).toHaveBeenCalledWith("stored_id", "stored_secret");
    expect(component.setState).toHaveBeenCalledWith({
      alert: { severity: "success", message: "Auth Loaded" },
    });
  });

  it("shows alert when storing auth without event key", () => {
    const component = new AuthTools({
      authId: "test_id",
      authSecret: "test_secret",
      manualEvent: true,
      selectedEvent: "",
      setAuth: mockSetAuth,
    });
    // Mock setState to capture the state change
    component.setState = jest.fn();
    component.storeAuth();
    expect(component.setState).toHaveBeenCalledWith({
      alert: { severity: "error", message: "You must enter an event key" },
    });
    expect(mockLocalStorage.setItem).not.toHaveBeenCalled();
  });

  it("shows alert when storing auth without credentials", () => {
    const component = new AuthTools({
      authId: "",
      authSecret: "",
      manualEvent: true,
      selectedEvent: "2024test",
      setAuth: mockSetAuth,
    });
    // Mock setState to capture the state change
    component.setState = jest.fn();
    component.storeAuth();
    expect(component.setState).toHaveBeenCalledWith({
      alert: {
        severity: "error",
        message: "You must enter you auth ID and secret",
      },
    });
    expect(mockLocalStorage.setItem).not.toHaveBeenCalled();
  });

  it("shows alert when loading auth with no stored data", () => {
    mockLocalStorage.getItem.mockReturnValue(null);
    const component = new AuthTools({
      authId: "",
      authSecret: "",
      manualEvent: true,
      selectedEvent: "2024test",
      setAuth: mockSetAuth,
    });
    // Mock setState to capture the state change
    component.setState = jest.fn();
    component.loadAuth();
    expect(component.setState).toHaveBeenCalledWith({
      alert: {
        severity: "error",
        message: "No auth found for 2024test",
      },
    });
    expect(mockSetAuth).not.toHaveBeenCalled();
  });

  it("shows alert when loading auth without event selected", () => {
    const component = new AuthTools({
      authId: "",
      authSecret: "",
      manualEvent: true,
      selectedEvent: "",
      setAuth: mockSetAuth,
    });
    // Mock setState to capture the state change
    component.setState = jest.fn();
    component.loadAuth();
    expect(component.setState).toHaveBeenCalledWith({
      alert: { severity: "error", message: "You must select an event" },
    });
    expect(mockLocalStorage.getItem).not.toHaveBeenCalled();
    expect(mockSetAuth).not.toHaveBeenCalled();
  });

  it("clears alert when clearAlert is called", () => {
    const component = new AuthTools({
      authId: "",
      authSecret: "",
      manualEvent: true,
      selectedEvent: "",
      setAuth: mockSetAuth,
    });
    // Mock setState
    component.setState = jest.fn();
    // Call clearAlert
    component.clearAlert();
    expect(component.setState).toHaveBeenCalledWith({ alert: null });
  });
});
