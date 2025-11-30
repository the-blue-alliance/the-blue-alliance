import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import AuthTools from "../AuthTools";

describe("AuthTools", () => {
  const mockSetAuth = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
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
});
