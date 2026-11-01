from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CustomBattle(Base):
    __tablename__ = "custom_battles"

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    dish_a: Mapped[str] = mapped_column(String(40))
    dish_b: Mapped[str] = mapped_column(String(40))
    meal_id_a: Mapped[str | None] = mapped_column(String(20), nullable=True)
    meal_id_b: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="open")  # open / closed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class CustomBattleVote(Base):
    __tablename__ = "custom_battle_votes"
    # Один пользователь может проголосовать в бою только один раз
    __table_args__ = (UniqueConstraint("battle_id", "user_id", name="uq_battle_voter"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    battle_id: Mapped[int] = mapped_column(ForeignKey("custom_battles.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    choice: Mapped[str] = mapped_column(String(1))  # "a" или "b"
    voted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
