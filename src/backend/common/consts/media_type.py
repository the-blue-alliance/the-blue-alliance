import enum


@enum.unique
class VideoType(str, enum.Enum):
    YOUTUBE = "youtube"
    TBA = "tba"
