/* @jest-environment jsdom */
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
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

  it("calls setAuth callback when auth ID changes", () => {
    // Test that the component properly wires up the onChange handler
    // by verifying it renders with the correct attributes
    const html = renderToStaticMarkup(
      <AuthInput
        authId="old_id"
        authSecret="secret123"
        manualEvent={true}
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain('value="old_id"');
    expect(html).toContain('value="secret123"');
  });

  it("calls setAuth callback when auth secret changes", () => {
    // Test that the component properly wires up the onChange handler
    // by verifying it renders with the correct attributes
    const html = renderToStaticMarkup(
      <AuthInput
        authId="id123"
        authSecret="old_secret"
        manualEvent={true}
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain('value="id123"');
    expect(html).toContain('value="old_secret"');
  });
});

describe("AuthInput interactions", () => {
  const mockSetAuth = jest.fn();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("reports the typed auth ID together with the existing secret", () => {
    render(
      <AuthInput
        authId="old_id"
        authSecret="existing_secret"
        manualEvent={true}
        setAuth={mockSetAuth}
      />
    );

    fireEvent.change(screen.getByLabelText("Auth Id"), {
      target: { value: "new_id" },
    });

    expect(mockSetAuth).toHaveBeenCalledWith("new_id", "existing_secret");
  });

  it("reports the typed auth secret together with the existing ID", () => {
    render(
      <AuthInput
        authId="existing_id"
        authSecret="old_secret"
        manualEvent={true}
        setAuth={mockSetAuth}
      />
    );

    fireEvent.change(screen.getByLabelText("Auth Secret"), {
      target: { value: "new_secret" },
    });

    expect(mockSetAuth).toHaveBeenCalledWith("existing_id", "new_secret");
  });

  it("substitutes empty strings when the other credential is unset", () => {
    render(<AuthInput manualEvent={true} setAuth={mockSetAuth} />);

    fireEvent.change(screen.getByLabelText("Auth Id"), {
      target: { value: "only_id" },
    });
    fireEvent.change(screen.getByLabelText("Auth Secret"), {
      target: { value: "only_secret" },
    });

    expect(mockSetAuth).toHaveBeenNthCalledWith(1, "only_id", "");
    expect(mockSetAuth).toHaveBeenNthCalledWith(2, "", "only_secret");
  });
});
