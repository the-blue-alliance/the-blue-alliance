"""
YouTube API helper methods for tasks_io service.
These methods interact with YouTube datafeeds and can only be used within tasks_io.
"""

import logging
from typing import Any, cast, Dict, Generator, List, Optional

from google.appengine.ext import ndb

from backend.common.helpers.youtube_video_helper import (
    YouTubeChannel,
    YouTubePlaylistItem,
    YouTubeUpcomingStream,
    YouTubeVideoHelper,
)
from backend.common.tasklets import typed_tasklet
from backend.tasks_io.datafeeds.datafeed_youtube import (
    YoutubePlaylistItemsDatafeed,
    YoutubeSearchDatafeed,
    YoutubeVideoDetailsDatafeed,
    YoutubeVideoLiveDetailsBatchDatafeed,
)


class YouTubeTasksIOHelper:
    """Helper class for YouTube operations that require datafeed access."""

    @classmethod
    @typed_tasklet
    def get_scheduled_start_time(
        cls, video_id: str
    ) -> Generator[Any, Any, Optional[str]]:
        """
        Fetches the scheduledStartTime for a YouTube video from the YouTube API.
        Returns the date in YYYY-MM-DD format, or None if not available.
        """
        try:
            datafeed = YoutubeVideoDetailsDatafeed(
                video_id,
                parts="liveStreamingDetails",
            )
            response = yield datafeed._fetch()

            if response.status_code != 200:
                raise ndb.Return(None)

            raw_data = cast(Optional[dict], response.json())
            if not raw_data or not raw_data.get("items"):
                raise ndb.Return(None)

            parsed_data = datafeed.parser().parse(raw_data)
            scheduled_start_time = (
                parsed_data.get("scheduled_start_time") if parsed_data else None
            )

            if not scheduled_start_time:
                live_details = raw_data["items"][0].get("liveStreamingDetails", {})
                scheduled_start_time = live_details.get("scheduledStartTime")

            if not scheduled_start_time:
                raise ndb.Return(None)

            raise ndb.Return(scheduled_start_time[:10])
        except ValueError:
            logging.warning(
                "No Google API secret, unable to fetch YouTube video details"
            )
            raise ndb.Return(None)
        except ndb.Return:
            raise
        except Exception:
            logging.exception(
                "Failed to fetch YouTube video scheduled start time for %s", video_id
            )
            raise ndb.Return(None)

    @classmethod
    @typed_tasklet
    def resolve_channel_name(
        cls, channel_name: str
    ) -> Generator[Any, Any, Optional[YouTubeChannel]]:
        """
        Resolves a YouTube channel name to a channel ID.
        Returns channel metadata if found, else None.
        """
        try:
            datafeed = YoutubeSearchDatafeed(
                query=channel_name,
                search_type="channel",
                max_results=1,
            )
            response = yield datafeed._fetch()

            if response.status_code != 200:
                raise ndb.Return(None)

            raw_data = cast(Optional[dict], response.json())
            if not raw_data or not raw_data.get("items"):
                raise ndb.Return(None)

            parsed_data = datafeed.parser().parse(raw_data)
            if parsed_data:
                first_item = parsed_data[0]
                resolved_channel_id = first_item.get("channel_id")
                resolved_channel_name = first_item.get("title")
            else:
                first_item = raw_data["items"][0]
                resolved_channel_id = first_item.get("id", {}).get("channelId")
                resolved_channel_name = first_item.get("snippet", {}).get("title")

            if not resolved_channel_id:
                raise ndb.Return(None)

            raise ndb.Return(
                YouTubeChannel(
                    channel_id=resolved_channel_id,
                    channel_name=resolved_channel_name or channel_name,
                )
            )
        except ValueError:
            logging.warning("No Google API secret, unable to resolve YouTube channel")
            raise ndb.Return(None)
        except ndb.Return:
            raise
        except Exception:
            logging.exception(
                "Failed to resolve YouTube channel name '%s'",
                channel_name,
            )
            raise ndb.Return(None)

    @classmethod
    @typed_tasklet
    def videos_in_playlist(
        cls, playlist_id: str
    ) -> Generator[Any, Any, List[YouTubePlaylistItem]]:
        """
        Fetches all videos in a YouTube playlist.
        Returns a list of video items with video_id, video_title, and guessed_match_partial.
        """
        videos: List[YouTubePlaylistItem] = []

        next_page_token = ""
        i = 0

        while i < 10:  # Prevent runaway looping
            try:
                datafeed = YoutubePlaylistItemsDatafeed(
                    playlist_id,
                    max_results=50,
                    page_token=next_page_token,
                )
            except ValueError:
                msg = "No Google API secret, unable to resolve playlist"
                logging.warning(msg)
                raise Exception(msg)

            try:
                response = yield datafeed._fetch()

                if response.status_code != 200:
                    error_msg = f"YouTube API returned status {response.status_code} for {response.url}. Response: {response.content[:500] if response.content else 'No content'}"
                    logging.error(error_msg)
                    raise Exception(
                        f"Unable to call YouTube API for videos in playlist '{playlist_id}': status {response.status_code}"
                    )
            except Exception as e:
                logging.exception(
                    "Unable to call YouTube API for videos in playlist '%s': %s",
                    playlist_id,
                    str(e),
                )
                raise

            video_result = cast(Optional[dict], response.json())
            if video_result is None:
                logging.error("YouTube API returned no data")
                break

            for video in datafeed.parser().parse(video_result):
                video_id = video.get("video_id")
                if not video_id:
                    continue
                video_title = video.get("title", "")
                videos.append(
                    YouTubePlaylistItem(
                        video_id=video_id,
                        video_title=video_title,
                        guessed_match_partial=YouTubeVideoHelper.guessMatchPartial(
                            video_title
                        ),
                    )
                )

            if "nextPageToken" not in video_result:
                break
            next_page_token = video_result["nextPageToken"]
            i += 1

        raise ndb.Return(videos)

    @classmethod
    @typed_tasklet
    def get_upcoming_streams(
        cls, channel_id: str
    ) -> Generator[Any, Any, List[YouTubeUpcomingStream]]:
        """
        Fetches all upcoming live streams for a given YouTube channel.
        Returns a list of streams with stream_id, title, and scheduled_start_time.
        """
        stream_basics: List[Dict[str, str]] = []
        try:
            search_datafeed = YoutubeSearchDatafeed(
                search_type="video",
                max_results=50,
                order="date",
                channel_id=channel_id,
                event_type="upcoming",
            )
            parsed_search_results = yield search_datafeed.fetch_all_pages_async()
        except ValueError:
            msg = "No Google API secret, unable to fetch upcoming streams"
            logging.warning(msg)
            raise Exception(msg)
        except Exception as e:
            logging.exception(
                "Unable to call YouTube API for upcoming streams in channel '%s': %s",
                channel_id,
                str(e),
            )
            raise Exception(
                f"Unable to call YouTube API for upcoming streams in channel '{channel_id}': {str(e)}"
            ) from e

        for item in parsed_search_results:
            video_id = item.get("video_id")
            if video_id:
                stream_basics.append(
                    {
                        "stream_id": video_id,
                        "title": item.get("title", ""),
                    }
                )

        streams: List[YouTubeUpcomingStream] = []
        for batch_start in range(0, len(stream_basics), 50):
            batch = stream_basics[batch_start : batch_start + 50]
            batch_datafeed = YoutubeVideoLiveDetailsBatchDatafeed(
                [stream["stream_id"] for stream in batch]
            )

            try:
                videos_response = yield batch_datafeed._fetch()

                if videos_response.status_code != 200:
                    logging.warning(
                        f"YouTube API videos endpoint returned status {videos_response.status_code} for {videos_response.url}. Response: {videos_response.content[:500] if videos_response.content else 'No content'}"
                    )
                    continue

                videos_result = cast(Optional[dict], videos_response.json())
                if videos_result is None:
                    logging.warning("YouTube videos API returned no data")
                    continue

                scheduled_times = batch_datafeed.parser().parse(videos_result)

                for stream in batch:
                    stream_id = stream["stream_id"]
                    streams.append(
                        YouTubeUpcomingStream(
                            stream_id=stream_id,
                            title=stream["title"],
                            scheduled_start_time=scheduled_times.get(stream_id, ""),
                        )
                    )
            except Exception:
                logging.exception("Unable to fetch video details from YouTube API")

        raise ndb.Return(streams)
