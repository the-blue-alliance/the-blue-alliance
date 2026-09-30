/* @jest-environment jsdom */
import React from "react";
import { render } from "@testing-library/react";
import WebcastEmbed from "../WebcastEmbed";

const baseWebcast = {
  key: "2026casj",
  num: 0,
  id: "2026casj-0",
  name: "Silicon Valley Regional",
  channel: "chan",
  file: "file",
};

const renderType = (type) => {
  const { container } = render(
    <WebcastEmbed webcast={{ ...baseWebcast, type }} />
  );
  return container;
};

describe("WebcastEmbed", () => {
  beforeEach(() => {
    global.videojs = jest.fn();
  });

  afterEach(() => {
    delete global.videojs;
  });

  it.each([
    ["ustream", "https://www.ustream.tv/embed/chan?html5ui=1"],
    ["youtube", "//www.youtube.com/embed/chan?autoplay=1"],
    [
      "twitch",
      `https://player.twitch.tv/?channel=chan&parent=${document.location.hostname}`,
    ],
    [
      "livestream",
      "https://new.livestream.com/accounts/chan/events/file/player?width=640&height=360&autoPlay=true&mute=false",
    ],
    ["dacast", "https://iframe.dacast.com/b/chan/c/file"],
  ])("embeds %s webcasts in an iframe", (type, src) => {
    const container = renderType(type);
    expect(container.querySelector("iframe").getAttribute("src")).toBe(src);
  });

  it("injects raw markup for iframe webcasts", () => {
    const { container } = render(
      <WebcastEmbed
        webcast={{ ...baseWebcast, type: "iframe", channel: "<b>hi</b>" }}
      />
    );
    expect(container.querySelector("b").textContent).toBe("hi");
  });

  it("uses video.js for html5 webcasts", () => {
    const container = renderType("html5");
    expect(container.querySelector("video source").getAttribute("type")).toBe(
      "application/x-mpegurl"
    );
  });

  it("uses video.js for rtmp webcasts", () => {
    const container = renderType("rtmp");
    expect(container.querySelector("video source").getAttribute("type")).toBe(
      "rtmp/mp4"
    );
  });

  it("shows a card with a link for direct_link webcasts", () => {
    const container = renderType("direct_link");
    expect(container.textContent).toContain("Webcast could not be embedded");
  });

  it("falls back to a not supported message for unknown types", () => {
    const container = renderType("hologram");
    expect(container.textContent).toContain("This webcast is not supported.");
  });
});
