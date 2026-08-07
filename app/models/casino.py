"""PC est magique Flask App - Casino Models"""

from __future__ import annotations

import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped

from app import db, models
from app.enums import PredictionStatus
from app.utils.columns import (
    column,
    one_to_many,
    many_to_one,
    my_enum,
    Column,
)

Enum = my_enum  # type checking hack

class Prediction(db.Model):
    """A prediction on which PCeens can bet."""
    
    __tablename__ = "prediction"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    name: Column[str] = column(sa.String(128), nullable=False)
    description: Column[str | None] = column(sa.String(1000), nullable=True)
    status: Column[PredictionStatus] = column(Enum(PredictionStatus), nullable=False, default=PredictionStatus.open)
    
    _author_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=False)
    author: Mapped["models.PCeen"] = many_to_one("PCeen.casino_predictions")
    
    _resolved_option_id: Column[int | None] = column(sa.ForeignKey("prediction_option.id"), nullable=True)
    resolved_option: Mapped["PredictionOption"] = many_to_one("PredictionOption.resolved_predictions", foreign_keys=[_resolved_option_id])
    
    options: Mapped[list["PredictionOption"]] = one_to_many("PredictionOption.prediction", cascade="all, delete-orphan", foreign_keys="PredictionOption._prediction_id")

    @property
    def total_pool(self) -> int:
        """Returns the total sum of bets for all options in this prediction."""
        return sum(option.total_pool for option in self.options)

class PredictionOption(db.Model):
    """An option for a Prediction."""
    
    __tablename__ = "prediction_option"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    _prediction_id: Column[int] = column(sa.ForeignKey("prediction.id"), nullable=False, index=True)
    prediction: Mapped["Prediction"] = many_to_one("Prediction.options", foreign_keys=[_prediction_id])
    name: Column[str] = column(sa.String(128), nullable=False)
    color: Column[str] = column(sa.String(7), nullable=False, default="#000000")
    
    resolved_predictions: Mapped[list["Prediction"]] = one_to_many("Prediction.resolved_option", foreign_keys="Prediction._resolved_option_id")
    bets: Mapped[list["Bet"]] = one_to_many("Bet.option", cascade="all, delete-orphan")

    @property
    def total_pool(self) -> int:
        """Returns the sum of bet amounts placed on this option."""
        return sum(bet.amount for bet in self.bets)

class Bet(db.Model):
    """A bet placed by a PCeen on a PredictionOption."""
    
    __tablename__ = "bet"
    id: Column[int] = column(sa.Integer(), primary_key=True)
    _pceen_id: Column[int] = column(sa.ForeignKey("pceen.id"), nullable=False, index=True)
    pceen: Mapped["models.PCeen"] = many_to_one("PCeen.casino_bets")
    
    _option_id: Column[int] = column(sa.ForeignKey("prediction_option.id"), nullable=False, index=True)
    option: Mapped["PredictionOption"] = many_to_one("PredictionOption.bets")
    
    amount: Column[int] = column(sa.Integer(), nullable=False)
    created_at: Column[datetime.datetime] = column(sa.DateTime(), nullable=False, default=lambda: datetime.datetime.now(datetime.UTC).replace(tzinfo=None))
