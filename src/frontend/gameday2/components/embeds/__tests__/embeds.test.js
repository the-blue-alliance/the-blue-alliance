/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";
import EmbedDacast from "../EmbedDacast";
import EmbedDirectLink from "../EmbedDirectLink";
import EmbedHtml5 from "../EmbedHtml5";
import EmbedIframe from "../EmbedIframe";
import EmbedLivestream from "../EmbedLivestream";
import EmbedNotSupported from "../EmbedNotSupported";
import EmbedRtmp from "../EmbedRtmp";
import EmbedTwitch from "../EmbedTwitch";
import EmbedUstream from "../EmbedUstream";
import EmbedYoutube from "../EmbedYoutube";

const webcast = {
  key: "2026casj",
  num: 0,
  id: "2026casj-0",
  name: "Silicon Valley Regional",
  type: "youtube",
  channel: "chan123",
  file: "file456",
};

describe("EmbedDacast", () => {
  it("embeds the dacast player for the channel and file", () => {
    const { container } = render(<EmbedDacast webcast={webcast} />);
    const iframe = container.querySelector("iframe");
    expect(iframe.getAttribute("src")).toBe(
      "https://iframe.dacast.com/b/chan123/c/file456"
    );
    expect(iframe.getAttribute("width")).toBe("100%");
    expect(iframe.getAttribute("height")).toBe("100%");
  });
});

describe("EmbedDirectLink", () => {
  it("explains the webcast cannot be embedded and links out to it", () => {
    const { getByText, getByRole } = render(
      <EmbedDirectLink
        webcast={{ ...webcast, channel: "https://example.com" }}
      />
    );
    expect(getByText("Webcast could not be embedded")).toBeTruthy();
    const link = getByRole("link", { name: "Open in new tab" });
    expect(link.getAttribute("href")).toBe("https://example.com");
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")).toBe("noopener noreferrer");
  });
});

describe("EmbedHtml5", () => {
  afterEach(() => {
    delete global.videojs;
  });

  it("renders a video.js player and initializes it on mount", () => {
    global.videojs = jest.fn();
    const { container } = render(<EmbedHtml5 webcast={webcast} />);
    const video = container.querySelector("video");
    expect(video.id).toBe("2026casj-0");
    expect(video.className).toBe("video-js vjs-default-skin");
    const source = video.querySelector("source");
    expect(source.getAttribute("src")).toBe("chan123");
    expect(source.getAttribute("type")).toBe("application/x-mpegurl");
    expect(global.videojs).toHaveBeenCalledWith("2026casj-0", {
      width: "100%",
      height: "100%",
      autoplay: true,
      crossorigin: "anonymous",
    });
  });
});

describe("EmbedIframe", () => {
  it("decodes the escaped markup and injects it", () => {
    const { container } = render(
      <EmbedIframe
        webcast={{
          ...webcast,
          channel: '&lt;iframe src="https://example.com/embed"&gt;',
        }}
      />
    );
    const iframe = container.querySelector("iframe");
    expect(iframe).not.toBeNull();
    expect(iframe.getAttribute("src")).toBe("https://example.com/embed");
  });

  it("Bug #38: decodes every &lt; and &gt; in the embed markup", () => {
    // Wrong today: .replace is called without the global flag, so only the
    // first &lt; and &gt; are decoded and the closing tag renders as text:
    // '<iframe src="x">&lt;/iframe&gt;</iframe>'.
    // Correct: all entities are decoded, giving a single empty iframe.
    const { container } = render(
      <EmbedIframe
        webcast={{
          ...webcast,
          channel: '&lt;iframe src="x"&gt;&lt;/iframe&gt;',
        }}
      />
    );
    expect(container.firstChild.innerHTML).toBe('<iframe src="x"></iframe>');
  });
});

describe("EmbedLivestream", () => {
  it("embeds the livestream player for the account and event", () => {
    const { container } = render(<EmbedLivestream webcast={webcast} />);
    const iframe = container.querySelector("iframe");
    expect(iframe.getAttribute("src")).toBe(
      "https://new.livestream.com/accounts/chan123/events/file456/player?width=640&height=360&autoPlay=true&mute=false"
    );
  });
});

describe("EmbedNotSupported", () => {
  it("shows a not supported message", () => {
    const { getByText } = render(<EmbedNotSupported />);
    expect(getByText("This webcast is not supported.")).toBeTruthy();
  });
});

describe("EmbedRtmp", () => {
  afterEach(() => {
    delete global.videojs;
  });

  it("renders an rtmp video.js player and initializes it on mount", () => {
    global.videojs = jest.fn();
    const { container } = render(<EmbedRtmp webcast={webcast} />);
    const source = container.querySelector("video source");
    expect(source.getAttribute("src")).toBe("rtmp://chan123&file456");
    expect(source.getAttribute("type")).toBe("rtmp/mp4");
    expect(global.videojs).toHaveBeenCalledWith("2026casj-0", {
      width: "100%",
      height: "100%",
      autoplay: true,
    });
  });
});

describe("EmbedTwitch", () => {
  it("embeds the twitch player with the current hostname as parent", () => {
    const { container } = render(<EmbedTwitch webcast={webcast} />);
    const iframe = container.querySelector("iframe");
    expect(iframe.getAttribute("src")).toBe(
      `https://player.twitch.tv/?channel=chan123&parent=${document.location.hostname}`
    );
  });
});

describe("EmbedUstream", () => {
  it("embeds the ustream player", () => {
    const { container } = render(<EmbedUstream webcast={webcast} />);
    const iframe = container.querySelector("iframe");
    expect(iframe.getAttribute("src")).toBe(
      "https://www.ustream.tv/embed/chan123?html5ui=1"
    );
    expect(iframe.style.borderWidth).toBe("0px");
    expect(iframe.style.borderColor).toBe("transparent");
  });
});

describe("EmbedYoutube", () => {
  it("embeds the autoplaying youtube player", () => {
    const { container } = render(<EmbedYoutube webcast={webcast} />);
    const iframe = container.querySelector("iframe");
    expect(iframe.getAttribute("src")).toBe(
      "//www.youtube.com/embed/chan123?autoplay=1"
    );
  });
});
