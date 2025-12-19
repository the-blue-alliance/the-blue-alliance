/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import AddRemoveWebcast from "../AddRemoveWebcast";
import { ApiEvent } from "../../../constants/ApiEvent";

describe("AddRemoveWebcast", () => {
  let mockAddWebcast: jest.Mock;
  let mockRemoveWebcast: jest.Mock;

  const mockEventWithWebcasts: ApiEvent = {
    key: "2020test",
    webcasts: [
      {
        type: "twitch",
        channel: "test_channel",
        url: "https://twitch.tv/test_channel",
        date: "2020-03-01",
      },
      {
        type: "youtube",
        channel: "test_yt",
        url: "https://youtube.com/watch?v=abc123",
      },
    ],
  };

  const mockEventWithoutWebcasts: ApiEvent = {
    key: "2020test",
    webcasts: [],
  };

  beforeEach(() => {
    mockAddWebcast = jest.fn();
    mockRemoveWebcast = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    test("renders label correctly", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText("Webcasts")).toBeInTheDocument();
    });

    test("renders webcast list when webcasts exist", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText("2 webcasts found")).toBeInTheDocument();
    });

    test("renders 'No webcasts found' when webcasts array is empty", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithoutWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText("No webcasts found")).toBeInTheDocument();
    });

    test("renders 'No webcasts found' when webcasts is undefined", () => {
      const eventWithoutWebcasts: ApiEvent = {
        key: "2020test",
      };

      render(
        <AddRemoveWebcast
          eventInfo={eventWithoutWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText("No webcasts found")).toBeInTheDocument();
    });

    test("renders 'No webcasts found' when eventInfo is null", () => {
      render(
        <AddRemoveWebcast
          eventInfo={null}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText("No webcasts found")).toBeInTheDocument();
    });

    test("renders URL input with placeholder", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByPlaceholderText("https://youtu.be/abc123")
      ).toBeInTheDocument();
    });

    test("renders date input with placeholder", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByPlaceholderText("2025-03-02 (optional)")
      ).toBeInTheDocument();
    });

    test("renders Add Webcast button", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText("Add Webcast")).toBeInTheDocument();
    });
  });

  describe("Input Fields", () => {
    test("URL input has correct id", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const urlInput = screen.getByPlaceholderText("https://youtu.be/abc123");
      expect(urlInput).toHaveAttribute("id", "webcast_url");
    });

    test("date input has correct id", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const dateInput = screen.getByPlaceholderText("2025-03-02 (optional)");
      expect(dateInput).toHaveAttribute("id", "webcast_date");
    });

    test("both inputs have form-control class", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const urlInput = screen.getByPlaceholderText("https://youtu.be/abc123");
      const dateInput = screen.getByPlaceholderText("2025-03-02 (optional)");
      
      expect(urlInput).toHaveClass("form-control");
      expect(dateInput).toHaveClass("form-control");
    });
  });

  describe("Disabled State", () => {
    test("inputs are disabled when eventInfo is null", () => {
      render(
        <AddRemoveWebcast
          eventInfo={null}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const urlInput = screen.getByPlaceholderText("https://youtu.be/abc123");
      const dateInput = screen.getByPlaceholderText("2025-03-02 (optional)");

      expect(urlInput).toBeDisabled();
      expect(dateInput).toBeDisabled();
    });

    test("button is disabled when eventInfo is null", () => {
      render(
        <AddRemoveWebcast
          eventInfo={null}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const button = screen.getByText("Add Webcast");
      expect(button).toBeDisabled();
    });

    test("inputs are enabled when eventInfo is provided", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const urlInput = screen.getByPlaceholderText("https://youtu.be/abc123");
      const dateInput = screen.getByPlaceholderText("2025-03-02 (optional)");

      expect(urlInput).not.toBeDisabled();
      expect(dateInput).not.toBeDisabled();
    });

    test("button is enabled when eventInfo is provided", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const button = screen.getByText("Add Webcast");
      expect(button).not.toBeDisabled();
    });
  });

  describe("User Interaction - URL Input", () => {
    test("URL input updates on change", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const urlInput = screen.getByPlaceholderText(
        "https://youtu.be/abc123"
      ) as HTMLInputElement;

      fireEvent.change(urlInput, {
        target: { value: "https://twitch.tv/newstream" },
      });

      expect(urlInput.value).toBe("https://twitch.tv/newstream");
    });

    test("URL input can be cleared", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const urlInput = screen.getByPlaceholderText(
        "https://youtu.be/abc123"
      ) as HTMLInputElement;

      fireEvent.change(urlInput, {
        target: { value: "https://test.com" },
      });
      fireEvent.change(urlInput, { target: { value: "" } });

      expect(urlInput.value).toBe("");
    });
  });

  describe("User Interaction - Date Input", () => {
    test("date input updates on change", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const dateInput = screen.getByPlaceholderText(
        "2025-03-02 (optional)"
      ) as HTMLInputElement;

      fireEvent.change(dateInput, { target: { value: "2025-03-15" } });

      expect(dateInput.value).toBe("2025-03-15");
    });

    test("date input can be left empty", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const dateInput = screen.getByPlaceholderText(
        "2025-03-02 (optional)"
      ) as HTMLInputElement;

      expect(dateInput.value).toBe("");
    });
  });

  describe("Add Webcast Functionality", () => {
    test("calls addWebcast with URL and date when button clicked", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const urlInput = screen.getByPlaceholderText("https://youtu.be/abc123");
      const dateInput = screen.getByPlaceholderText("2025-03-02 (optional)");
      const button = screen.getByText("Add Webcast");

      fireEvent.change(urlInput, {
        target: { value: "https://youtube.com/watch?v=xyz" },
      });
      fireEvent.change(dateInput, { target: { value: "2025-04-01" } });
      fireEvent.click(button);

      expect(mockAddWebcast).toHaveBeenCalledTimes(1);
      expect(mockAddWebcast).toHaveBeenCalledWith(
        "https://youtube.com/watch?v=xyz",
        "2025-04-01"
      );
    });

    test("calls addWebcast with URL only when date is empty", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const urlInput = screen.getByPlaceholderText("https://youtu.be/abc123");
      const button = screen.getByText("Add Webcast");

      fireEvent.change(urlInput, {
        target: { value: "https://twitch.tv/stream" },
      });
      fireEvent.click(button);

      expect(mockAddWebcast).toHaveBeenCalledTimes(1);
      expect(mockAddWebcast).toHaveBeenCalledWith(
        "https://twitch.tv/stream",
        ""
      );
    });

    test("clears inputs after adding webcast", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const urlInput = screen.getByPlaceholderText(
        "https://youtu.be/abc123"
      ) as HTMLInputElement;
      const dateInput = screen.getByPlaceholderText(
        "2025-03-02 (optional)"
      ) as HTMLInputElement;
      const button = screen.getByText("Add Webcast");

      fireEvent.change(urlInput, {
        target: { value: "https://test.com" },
      });
      fireEvent.change(dateInput, { target: { value: "2025-01-01" } });
      fireEvent.click(button);

      expect(urlInput.value).toBe("");
      expect(dateInput.value).toBe("");
    });

    test("can add webcast with empty URL", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const button = screen.getByText("Add Webcast");
      fireEvent.click(button);

      expect(mockAddWebcast).toHaveBeenCalledTimes(1);
      expect(mockAddWebcast).toHaveBeenCalledWith("", "");
    });

    test("can add multiple webcasts", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const urlInput = screen.getByPlaceholderText("https://youtu.be/abc123");
      const button = screen.getByText("Add Webcast");

      fireEvent.change(urlInput, { target: { value: "https://test1.com" } });
      fireEvent.click(button);

      fireEvent.change(urlInput, { target: { value: "https://test2.com" } });
      fireEvent.click(button);

      expect(mockAddWebcast).toHaveBeenCalledTimes(2);
    });
  });

  describe("Button Styling", () => {
    test("Add Webcast button has correct class", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const button = screen.getByText("Add Webcast");
      expect(button).toHaveClass("btn", "btn-info");
    });
  });

  describe("Form Group Structure", () => {
    test("renders within form-group row", () => {
      const { container } = render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const formGroup = container.querySelector(".form-group.row");
      expect(formGroup).toBeInTheDocument();
    });

    test("label has correct column class", () => {
      render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const label = screen.getByText("Webcasts");
      expect(label).toHaveClass("col-sm-2", "control-label");
    });

    test("webcast list has correct id", () => {
      const { container } = render(
        <AddRemoveWebcast
          eventInfo={mockEventWithWebcasts}
          addWebcast={mockAddWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const webcastList = container.querySelector("#webcast_list");
      expect(webcastList).toBeInTheDocument();
      expect(webcastList).toHaveClass("col-sm-10");
    });
  });
});
