/* @jest-environment jsdom */
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
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
    expect(html).toContain("btn");
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

  it("handles store auth action", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId="test_id"
        authSecret="test_secret"
        manualEvent={true}
        selectedEvent="2024test"
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain("Store Auth");
    expect(html).toContain("form-group");
  });

  it("handles load auth action", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId=""
        authSecret=""
        manualEvent={true}
        selectedEvent="2024test"
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain("Load Auth");
    expect(html).toContain("form-group");
  });

  it("renders with no event selected", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId="test_id"
        authSecret="test_secret"
        manualEvent={true}
        selectedEvent=""
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain("Auth Tools");
    expect(html).toContain("Store Auth");
  });

  it("renders with auth credentials populated", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId="my_id"
        authSecret="my_secret"
        manualEvent={true}
        selectedEvent="2024test"
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain("Auth Tools");
    expect(html).toContain("btn");
  });

  it("renders with no auth credentials", () => {
    const html = renderToStaticMarkup(
      <AuthTools
        authId=""
        authSecret=""
        manualEvent={true}
        selectedEvent="2024test"
        setAuth={mockSetAuth}
      />
    );
    expect(html).toContain("Auth Tools");
    expect(html).toContain("Load Auth");
  });
});

describe("AuthTools interactions", () => {
  const mockSetAuth = jest.fn();

  const renderTools = (
    overrides: Partial<React.ComponentProps<typeof AuthTools>> = {}
  ) =>
    render(
      <AuthTools
        authId="test_id"
        authSecret="test_secret"
        manualEvent={true}
        selectedEvent="2024test"
        setAuth={mockSetAuth}
        {...overrides}
      />
    );

  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Store Auth", () => {
    it("rejects storing when no event key has been entered", () => {
      renderTools({ selectedEvent: "" });

      fireEvent.click(screen.getByRole("button", { name: "Store Auth" }));

      expect(screen.getByRole("alert")).toHaveTextContent(
        "You must enter an event key"
      );
      expect(localStorage.length).toBe(0);
    });

    it("rejects storing when the auth ID is missing", () => {
      renderTools({ authId: "" });

      fireEvent.click(screen.getByRole("button", { name: "Store Auth" }));

      expect(screen.getByRole("alert")).toHaveTextContent(
        "You must enter you auth ID and secret"
      );
      expect(localStorage.length).toBe(0);
    });

    it("rejects storing when the auth secret is missing", () => {
      renderTools({ authSecret: "" });

      fireEvent.click(screen.getByRole("button", { name: "Store Auth" }));

      expect(screen.getByRole("alert")).toHaveTextContent(
        "You must enter you auth ID and secret"
      );
      expect(localStorage.length).toBe(0);
    });

    it("persists the credentials under the event key", () => {
      renderTools();

      fireEvent.click(screen.getByRole("button", { name: "Store Auth" }));

      expect(JSON.parse(localStorage.getItem("2024test_auth") || "")).toEqual({
        id: "test_id",
        secret: "test_secret",
      });
      expect(screen.getByRole("alert")).toHaveTextContent("Auth Stored");
    });
  });

  describe("Load Auth", () => {
    it("rejects loading when no event is selected", () => {
      renderTools({ selectedEvent: "" });

      fireEvent.click(screen.getByText("Load Auth"));

      expect(screen.getByRole("alert")).toHaveTextContent(
        "You must select an event"
      );
      expect(mockSetAuth).not.toHaveBeenCalled();
    });

    it("reports when nothing is stored for the event", () => {
      renderTools();

      fireEvent.click(screen.getByText("Load Auth"));

      expect(screen.getByRole("alert")).toHaveTextContent(
        "No auth found for 2024test"
      );
      expect(mockSetAuth).not.toHaveBeenCalled();
    });

    it("restores stored credentials through setAuth", () => {
      localStorage.setItem(
        "2024test_auth",
        JSON.stringify({ id: "stored_id", secret: "stored_secret" })
      );
      renderTools({ authId: "", authSecret: "" });

      fireEvent.click(screen.getByText("Load Auth"));

      expect(mockSetAuth).toHaveBeenCalledWith("stored_id", "stored_secret");
      expect(screen.getByRole("alert")).toHaveTextContent("Auth Loaded");
    });
  });

  it("dismisses the alert when it is closed", () => {
    renderTools();
    fireEvent.click(screen.getByRole("button", { name: "Store Auth" }));
    expect(screen.getByRole("alert")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
