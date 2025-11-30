import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import AuthInput from "../AuthInput";

describe("AuthInput", () => {
  const mockSetAuth = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders nothing when manualEvent is false", () => {
    const html = renderToStaticMarkup(
      <AuthInput
        authId=""
        authSecret=""
        manualEvent={false}
        setAuth={mockSetAuth}
      />
    );
    expect(html).toBe("");
  });

  it("renders auth input fields when manualEvent is true", () => {
    const html = renderToStaticMarkup(
      <AuthInput
        authId="test_id"
        authSecret="test_secret"
        manualEvent={true}
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain('id="auth-container"');
    expect(html).toContain('id="auth_id"');
    expect(html).toContain('id="auth_secret"');
  });

  it("renders Auth Id label and input", () => {
    const html = renderToStaticMarkup(
      <AuthInput
        authId="test_id"
        authSecret=""
        manualEvent={true}
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain("Auth Id");
    expect(html).toContain('placeholder="Auth ID"');
    expect(html).toContain('value="test_id"');
  });

  it("renders Auth Secret label and input", () => {
    const html = renderToStaticMarkup(
      <AuthInput
        authId=""
        authSecret="test_secret"
        manualEvent={true}
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain("Auth Secret");
    expect(html).toContain('placeholder="Auth Secret"');
    expect(html).toContain('value="test_secret"');
  });

  it("renders password type inputs", () => {
    const html = renderToStaticMarkup(
      <AuthInput
        authId=""
        authSecret=""
        manualEvent={true}
        setAuth={mockSetAuth}
      />
    );
    expect(html).toMatch(/type="password"/g);
  });

  it("uses form-control class on inputs", () => {
    const html = renderToStaticMarkup(
      <AuthInput
        authId=""
        authSecret=""
        manualEvent={true}
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain("form-control");
  });

  it("displays empty values when auth is not set", () => {
    const html = renderToStaticMarkup(
      <AuthInput
        authId=""
        authSecret=""
        manualEvent={true}
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain('value=""');
  });

  it("wires onChange handler to auth ID input", () => {
    const component = new AuthInput({
      authId: "old_id",
      authSecret: "secret123",
      manualEvent: true,
      setAuth: mockSetAuth,
    });
    component.onAuthIdChange({ target: { value: "new_id" } });
    expect(mockSetAuth).toHaveBeenCalledWith("new_id", "secret123");
  });

  it("wires onChange handler to auth secret input", () => {
    const component = new AuthInput({
      authId: "id123",
      authSecret: "old_secret",
      manualEvent: true,
      setAuth: mockSetAuth,
    });
    component.onAuthSecretChange({ target: { value: "new_secret" } });
    expect(mockSetAuth).toHaveBeenCalledWith("id123", "new_secret");
  });
});
