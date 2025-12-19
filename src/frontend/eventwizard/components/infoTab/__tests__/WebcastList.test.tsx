/* @jest-environment jsdom */

import React from "react";
import "@testing-library/jest-dom";
import { render, screen, fireEvent } from "@testing-library/react";
import WebcastList from "../WebcastList";
import { ApiWebcast } from "../../../constants/ApiWebcast";

describe("WebcastList", () => {
  let mockRemoveWebcast: jest.Mock;

  const mockWebcasts: ApiWebcast[] = [
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
    {
      type: "livestream",
      channel: "test_stream",
    },
  ];

  beforeEach(() => {
    mockRemoveWebcast = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe("Rendering", () => {
    test("renders count message with correct number", () => {
      render(
        <WebcastList
          webcasts={mockWebcasts}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText("3 webcasts found")).toBeInTheDocument();
    });

    test("renders count message for single webcast", () => {
      const singleWebcast = [mockWebcasts[0]];

      render(
        <WebcastList
          webcasts={singleWebcast}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText("1 webcasts found")).toBeInTheDocument();
    });

    test("does not render count message when webcasts array is empty", () => {
      render(<WebcastList webcasts={[]} removeWebcast={mockRemoveWebcast} />);

      expect(screen.queryByText(/webcasts found/)).not.toBeInTheDocument();
    });

    test("renders unordered list", () => {
      const { container } = render(
        <WebcastList
          webcasts={mockWebcasts}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const ul = container.querySelector("ul");
      expect(ul).toBeInTheDocument();
    });

    test("renders correct number of list items", () => {
      const { container } = render(
        <WebcastList
          webcasts={mockWebcasts}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const listItems = container.querySelectorAll("li");
      expect(listItems).toHaveLength(3);
    });

    test("renders WebcastItem for each webcast", () => {
      render(
        <WebcastList
          webcasts={mockWebcasts}
          removeWebcast={mockRemoveWebcast}
        />
      );

      // Check that all webcasts are rendered
      expect(
        screen.getByText("https://twitch.tv/test_channel (2020-03-01)")
      ).toBeInTheDocument();
      expect(
        screen.getByText("https://youtube.com/watch?v=abc123")
      ).toBeInTheDocument();
      expect(
        screen.getByText("livestream - test_stream")
      ).toBeInTheDocument();
    });
  });

  describe("Empty State", () => {
    test("renders empty list when no webcasts", () => {
      const { container } = render(
        <WebcastList webcasts={[]} removeWebcast={mockRemoveWebcast} />
      );

      const ul = container.querySelector("ul");
      expect(ul).toBeInTheDocument();
      expect(ul?.children).toHaveLength(0);
    });
  });

  describe("Remove Functionality", () => {
    test("passes removeWebcast function to WebcastItem", () => {
      render(
        <WebcastList
          webcasts={mockWebcasts}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const removeButtons = screen.getAllByText("Remove");
      expect(removeButtons).toHaveLength(3);
    });

    test("clicking remove on first item calls removeWebcast with index 0", () => {
      render(
        <WebcastList
          webcasts={mockWebcasts}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const removeButtons = screen.getAllByText("Remove");
      fireEvent.click(removeButtons[0]);

      expect(mockRemoveWebcast).toHaveBeenCalledTimes(1);
      expect(mockRemoveWebcast).toHaveBeenCalledWith(0);
    });

    test("clicking remove on second item calls removeWebcast with index 1", () => {
      render(
        <WebcastList
          webcasts={mockWebcasts}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const removeButtons = screen.getAllByText("Remove");
      fireEvent.click(removeButtons[1]);

      expect(mockRemoveWebcast).toHaveBeenCalledTimes(1);
      expect(mockRemoveWebcast).toHaveBeenCalledWith(1);
    });

    test("clicking remove on third item calls removeWebcast with index 2", () => {
      render(
        <WebcastList
          webcasts={mockWebcasts}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const removeButtons = screen.getAllByText("Remove");
      fireEvent.click(removeButtons[2]);

      expect(mockRemoveWebcast).toHaveBeenCalledTimes(1);
      expect(mockRemoveWebcast).toHaveBeenCalledWith(2);
    });
  });

  describe("Webcast Ordering", () => {
    test("renders webcasts in the order provided", () => {
      const { container } = render(
        <WebcastList
          webcasts={mockWebcasts}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const listItems = container.querySelectorAll("li");
      
      // Check first item
      expect(listItems[0]).toHaveTextContent("https://twitch.tv/test_channel");
      
      // Check second item
      expect(listItems[1]).toHaveTextContent("https://youtube.com/watch?v=abc123");
      
      // Check third item
      expect(listItems[2]).toHaveTextContent("livestream - test_stream");
    });
  });

  describe("Webcast with Different Properties", () => {
    test("renders webcast with URL", () => {
      const webcastsWithUrl: ApiWebcast[] = [
        {
          type: "youtube",
          channel: "test",
          url: "https://youtube.com/watch?v=test",
        },
      ];

      render(
        <WebcastList
          webcasts={webcastsWithUrl}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByText("https://youtube.com/watch?v=test")
      ).toBeInTheDocument();
    });

    test("renders webcast with type and channel when no URL", () => {
      const webcastsWithoutUrl: ApiWebcast[] = [
        {
          type: "twitch",
          channel: "my_channel",
        },
      ];

      render(
        <WebcastList
          webcasts={webcastsWithoutUrl}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(screen.getByText("twitch - my_channel")).toBeInTheDocument();
    });

    test("renders webcast with date when provided", () => {
      const webcastsWithDate: ApiWebcast[] = [
        {
          type: "youtube",
          channel: "test",
          url: "https://youtube.com/watch?v=test",
          date: "2025-03-15",
        },
      ];

      render(
        <WebcastList
          webcasts={webcastsWithDate}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByText("https://youtube.com/watch?v=test (2025-03-15)")
      ).toBeInTheDocument();
    });

    test("renders webcast without date when not provided", () => {
      const webcastsWithoutDate: ApiWebcast[] = [
        {
          type: "youtube",
          channel: "test",
          url: "https://youtube.com/watch?v=test",
        },
      ];

      render(
        <WebcastList
          webcasts={webcastsWithoutDate}
          removeWebcast={mockRemoveWebcast}
        />
      );

      expect(
        screen.getByText("https://youtube.com/watch?v=test")
      ).toBeInTheDocument();
    });
  });

  describe("List Keys", () => {
    test("renders unique list items for each webcast", () => {
      const { container } = render(
        <WebcastList
          webcasts={mockWebcasts}
          removeWebcast={mockRemoveWebcast}
        />
      );

      const listItems = container.querySelectorAll("li");
      
      // Each webcast should have its own list item (keys handled internally by React)
      expect(listItems).toHaveLength(mockWebcasts.length);
    });
  });
});
