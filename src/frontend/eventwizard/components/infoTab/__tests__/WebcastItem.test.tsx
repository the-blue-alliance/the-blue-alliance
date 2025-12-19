/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import WebcastItem from "../WebcastItem";
import { ApiWebcast } from "../../../constants/ApiWebcast";

describe("WebcastItem", () => {
  let mockRemoveWebcast: jest.Mock;

  beforeEach(() => {
    mockRemoveWebcast = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering with URL", () => {
    test("renders webcast URL when URL is provided", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test_channel",
        url: "https://youtube.com/watch?v=abc123",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByText("https://youtube.com/watch?v=abc123", { exact: false })
      ).toBeInTheDocument();
    });

    test("renders webcast URL with date when both are provided", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test_channel",
        url: "https://youtube.com/watch?v=abc123",
        date: "2020-03-01",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByText("https://youtube.com/watch?v=abc123 (2020-03-01)", {
          exact: false,
        })
      ).toBeInTheDocument();
    });

    test("prefers URL over type-channel when URL exists", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "should_not_show",
        url: "https://youtube.com/watch?v=shown",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText(/https:\/\/youtube.com/)).toBeInTheDocument();
      expect(screen.queryByText(/should_not_show/)).not.toBeInTheDocument();
    });
  });

  describe("Rendering without URL", () => {
    test("renders type and channel when URL is not provided", () => {
      const webcast: ApiWebcast = {
        type: "twitch",
        channel: "test_channel",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByText("twitch - test_channel", { exact: false })
      ).toBeInTheDocument();
    });

    test("renders type-channel with date when provided", () => {
      const webcast: ApiWebcast = {
        type: "livestream",
        channel: "my_stream",
        date: "2025-04-15",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByText("livestream - my_stream (2025-04-15)", { exact: false })
      ).toBeInTheDocument();
    });
  });

  describe("Date Display", () => {
    test("displays date in parentheses when provided", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/watch?v=test",
        date: "2020-03-01",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText(/(2020-03-01)/)).toBeInTheDocument();
    });

    test("does not display date when not provided", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/watch?v=test",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.queryByText(/\(/)).not.toBeInTheDocument();
    });

    test("handles undefined date", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/watch?v=test",
        date: undefined,
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.queryByText(/\(/)).not.toBeInTheDocument();
    });
  });

  describe("Remove Button", () => {
    test("renders Remove button", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/watch?v=test",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const button = screen.getByText("Remove");
      expect(button).toBeInTheDocument();
    });

    test("Remove button has correct classes", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/watch?v=test",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const button = screen.getByText("Remove");
      expect(button).toHaveClass("btn", "btn-danger");
    });

    test("clicking Remove button calls removeWebcast with correct index", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/watch?v=test",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={5}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const button = screen.getByText("Remove");
      fireEvent.click(button);

      expect(mockRemoveWebcast).toHaveBeenCalledTimes(1);
      expect(mockRemoveWebcast).toHaveBeenCalledWith(5);
    });

    test("clicking Remove button multiple times calls removeWebcast each time", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/watch?v=test",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={2}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const button = screen.getByText("Remove");
      fireEvent.click(button);
      fireEvent.click(button);
      fireEvent.click(button);

      expect(mockRemoveWebcast).toHaveBeenCalledTimes(3);
    });
  });

  describe("Different Webcast Types", () => {
    test("renders Twitch webcast", () => {
      const webcast: ApiWebcast = {
        type: "twitch",
        channel: "my_twitch_channel",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByText("twitch - my_twitch_channel", { exact: false })
      ).toBeInTheDocument();
    });

    test("renders YouTube webcast", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "my_youtube_channel",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByText("youtube - my_youtube_channel", { exact: false })
      ).toBeInTheDocument();
    });

    test("renders livestream webcast", () => {
      const webcast: ApiWebcast = {
        type: "livestream",
        channel: "my_livestream_channel",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByText("livestream - my_livestream_channel", { exact: false })
      ).toBeInTheDocument();
    });
  });

  describe("Index Handling", () => {
    test("handles index 0", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/test",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      fireEvent.click(screen.getByText("Remove"));
      expect(mockRemoveWebcast).toHaveBeenCalledWith(0);
    });

    test("handles large index", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/test",
      };

      render(
        <WebcastItem
          webcast={webcast}
          index={999}
          removeWebcast={mockRemoveWebcast}
        />
      );

      fireEvent.click(screen.getByText("Remove"));
      expect(mockRemoveWebcast).toHaveBeenCalledWith(999);
    });
  });

  describe("Rendering Structure", () => {
    test("wraps content in paragraph tag", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/test",
      };

      const { container } = render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const paragraph = container.querySelector("p");
      expect(paragraph).toBeInTheDocument();
      expect(paragraph).toHaveTextContent("https://youtube.com/test");
    });

    test("button is inside paragraph", () => {
      const webcast: ApiWebcast = {
        type: "youtube",
        channel: "test",
        url: "https://youtube.com/test",
      };

      const { container } = render(
        <WebcastItem
          webcast={webcast}
          index={0}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const paragraph = container.querySelector("p");
      const button = screen.getByText("Remove");
      
      expect(paragraph).toContainElement(button);
    });
  });
});
