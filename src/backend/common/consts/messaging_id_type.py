import enum


@enum.unique
class MessagingIdType(enum.IntEnum):
    TOKEN = 0
    FID = 1


NAMES: dict[MessagingIdType, str] = {
    MessagingIdType.TOKEN: "token",
    MessagingIdType.FID: "fid",
}


ENUMS: dict[str, MessagingIdType] = {
    "token": MessagingIdType.TOKEN,
    "fid": MessagingIdType.FID,
}
