from backend.common.models.tba_video import TBAVideo


def test_paths() -> None:
    video = TBAVideo("2010ct", "2010ct_qm1", ["jpg", "mp4", "avi"])
    assert (
        video.thumbnail_path
        == "http://videos.thebluealliance.net/2010ct/2010ct_qm1.jpg"
    )
    assert (
        video.streamable_path
        == "http://videos.thebluealliance.net/2010ct/2010ct_qm1.mp4"
    )
    # Filetype preference order wins over the order the videos were listed in
    assert (
        video.downloadable_path
        == "http://videos.thebluealliance.net/2010ct/2010ct_qm1.mp4"
    )


def test_paths_missing_filetypes() -> None:
    video = TBAVideo("2010ct", "2010ct_qm1", ["mov"])
    assert video.thumbnail_path is None
    assert video.streamable_path is None
    assert (
        video.downloadable_path
        == "http://videos.thebluealliance.net/2010ct/2010ct_qm1.mov"
    )

    no_videos = TBAVideo("2010ct", "2010ct_qm1", [])
    assert no_videos.thumbnail_path is None
    assert no_videos.streamable_path is None
    assert no_videos.downloadable_path is None
