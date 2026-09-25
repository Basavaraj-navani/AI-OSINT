from collections.abc import AsyncIterator
from datetime import datetime
from importlib import import_module
from typing import Protocol, cast


class TelethonMessage(Protocol):
    id: int | None
    text: str | None
    media: object | None
    date: datetime
    views: int | None
    forwards: int | None
    edit_date: datetime | None
    chat: object | None
    chat_id: int | None
    sender: object | None
    sender_id: int | None
    replies: object | None
    from_id: object | None
    action: object | None
    deleted: bool


class TelethonPhotoMedia(Protocol):
    photo: object


class TelethonDocumentMedia(Protocol):
    document: object


class TelethonFloodWaitError(Protocol):
    seconds: int


class TelethonClient(Protocol):
    def is_connected(self) -> bool: ...

    async def is_user_authorized(self) -> bool: ...

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...

    async def get_entity(self, entity: object) -> object: ...

    def iter_messages(self, entity: object, limit: int = 100) -> AsyncIterator[TelethonMessage]: ...

    async def download_media(self, message: object, file: str) -> object | None: ...


class TelethonClientFactory(Protocol):
    def __call__(self, *, session: str, api_id: int, api_hash: str) -> TelethonClient: ...


def _module_type(module_name: str, type_name: str) -> type[object]:
    return cast("type[object]", getattr(import_module(module_name), type_name))


def telethon_client_type() -> TelethonClientFactory:
    return cast("TelethonClientFactory", _module_type("telethon", "TelegramClient"))


def telethon_auth_error_type() -> type[Exception]:
    return cast("type[Exception]", _module_type("telethon.errors", "AuthKeyUnregisteredError"))


def telethon_media_type(type_name: str) -> type[object]:
    return _module_type("telethon.tl.types", type_name)


TELETHON_MESSAGE_MEDIA_DOCUMENT = telethon_media_type("MessageMediaDocument")
TELETHON_MESSAGE_MEDIA_PHOTO = telethon_media_type("MessageMediaPhoto")
TELETHON_MESSAGE_MEDIA_WEB_PAGE = telethon_media_type("MessageMediaWebPage")
