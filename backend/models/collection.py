from __future__ import annotations

import base64
import json

from config import FRONTEND_RESOURCES_PATH
from models.base import BaseModel
from models.rom import Rom
from models.user import User
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from utils.database import CustomJSON


class Collection(BaseModel):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(length=400))
    description: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(default=False)
    path_cover_l: Mapped[str | None] = mapped_column(Text, default="")
    path_cover_s: Mapped[str | None] = mapped_column(Text, default="")
    url_cover: Mapped[str | None] = mapped_column(
        Text, default="", doc="URL to cover image stored in IGDB"
    )

    roms: Mapped[list[Rom]] = relationship(
        "Rom",
        secondary="collections_roms",
        collection_class=set,
        back_populates="collections",
        lazy="joined",
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped[User] = relationship(lazy="joined", back_populates="collections")

    @property
    def user__username(self) -> str:
        return self.user.username

    @property
    def rom_ids(self) -> list[int]:
        return [r.id for r in self.roms]

    @property
    def rom_count(self) -> int:
        return len(self.roms)

    @property
    def fs_resources_path(self) -> str:
        return f"collections/{str(self.id)}"

    @property
    def path_cover_small(self) -> str | None:
        return (
            f"{FRONTEND_RESOURCES_PATH}/{self.path_cover_s}?ts={self.updated_at}"
            if self.path_cover_s
            else None
        )

    @property
    def path_cover_large(self) -> str | None:
        return (
            f"{FRONTEND_RESOURCES_PATH}/{self.path_cover_l}?ts={self.updated_at}"
            if self.path_cover_l
            else None
        )

    @property
    def path_covers_small(self) -> list[str]:
        return [
            f"{FRONTEND_RESOURCES_PATH}/{r.path_cover_s}?ts={self.updated_at}"
            for r in self.roms
            if r.path_cover_s
        ]

    @property
    def path_covers_large(self) -> list[str]:
        return [
            f"{FRONTEND_RESOURCES_PATH}/{r.path_cover_l}?ts={self.updated_at}"
            for r in self.roms
            if r.path_cover_l
        ]

    @property
    def is_favorite(self) -> bool:
        return self.name.lower() == "favourites"

    def __repr__(self) -> str:
        return self.name


class CollectionRom(BaseModel):
    __tablename__ = "collections_roms"

    collection_id: Mapped[int] = mapped_column(
        ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True
    )
    rom_id: Mapped[int] = mapped_column(
        ForeignKey("roms.id", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (
        UniqueConstraint("collection_id", "rom_id", name="unique_collection_rom"),
    )


class VirtualCollection(BaseModel):
    __tablename__ = "virtual_collections"

    name: Mapped[str] = mapped_column(String(length=400), primary_key=True)
    type: Mapped[str] = mapped_column(String(length=50), primary_key=True)
    description: Mapped[str | None] = mapped_column(Text)
    path_covers_s: Mapped[list[str]] = mapped_column(CustomJSON(), default=[])
    path_covers_l: Mapped[list[str]] = mapped_column(CustomJSON(), default=[])

    rom_ids: Mapped[set[int]] = mapped_column(
        CustomJSON(), default=[], doc="Rom IDs that belong to this collection"
    )

    @property
    def id(self) -> str:
        # Create a reversible encoded ID
        data = json.dumps({"name": self.name, "type": self.type})
        return base64.urlsafe_b64encode(data.encode()).decode()

    @classmethod
    def from_id(cls, id_: str):
        data = json.loads(base64.urlsafe_b64decode(id_).decode())
        return data["name"], data["type"]

    @property
    def rom_count(self) -> int:
        return len(self.rom_ids)

    @property
    def path_cover_small(self) -> str | None:
        return None

    @property
    def path_cover_large(self) -> str | None:
        return None

    @property
    def path_covers_small(self) -> list[str]:
        return [
            f"{FRONTEND_RESOURCES_PATH}/{cover}?ts={self.updated_at}"
            for cover in self.path_covers_s
        ]

    @property
    def path_covers_large(self) -> list[str]:
        return [
            f"{FRONTEND_RESOURCES_PATH}/{cover}?ts={self.updated_at}"
            for cover in self.path_covers_l
        ]

    __table_args__ = (
        UniqueConstraint(
            "name",
            "type",
            name="unique_virtual_collection_name_type",
        ),
    )
