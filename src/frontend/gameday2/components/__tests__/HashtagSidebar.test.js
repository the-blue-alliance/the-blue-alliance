/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";
import HashtagSidebar from "../HashtagSidebar";

describe("HashtagSidebar", () => {
  let anchor;

  beforeEach(() => {
    // The twitter embed code inserts its script before the first <script> on
    // the page, so jsdom needs one to exist.
    anchor = document.createElement("script");
    document.head.appendChild(anchor);
  });

  afterEach(() => {
    anchor.remove();
    const script = document.getElementById("twitter-wjs");
    if (script) {
      script.remove();
    }
  });

  it("renders the #omgrobots timeline and injects the twitter widget script once", () => {
    const { container, getByText, unmount } = render(
      <HashtagSidebar enabled />
    );
    expect(container.firstChild.className).toBe("hashtag-sidebar");
    expect(container.firstChild.style.display).toBe("");
    expect(getByText("Tweets about #omgrobots").getAttribute("href")).toBe(
      "https://twitter.com/search?q=%23omgrobots"
    );

    const script = document.getElementById("twitter-wjs");
    expect(script.src).toBe("http://platform.twitter.com/widgets.js");
    expect(script.nextSibling).toBe(anchor);

    // Mounting again must not add a second copy of the script
    unmount();
    render(<HashtagSidebar enabled />);
    expect(document.querySelectorAll("#twitter-wjs")).toHaveLength(1);
  });

  it("hides the sidebar when disabled", () => {
    const { container } = render(<HashtagSidebar enabled={false} />);
    expect(container.firstChild.style.display).toBe("none");
  });
});
