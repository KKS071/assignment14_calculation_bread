# File: app/models/calculation.py
# Purpose: SQLAlchemy models for calculations — single-table polymorphic inheritance.
#          All operations accept a list of 2+ floats (multi-value support).
import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declared_attr, relationship

from app.database import Base


class AbstractCalculation:
    """Shared columns and logic for all calculation types."""

    @declared_attr
    def __tablename__(cls):
        return "calculations"

    @declared_attr
    def id(cls):
        return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)

    @declared_attr
    def user_id(cls):
        return Column(
            UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )

    @declared_attr
    def type(cls):
        return Column(String(50), nullable=False, index=True)

    @declared_attr
    def inputs(cls):
        return Column(JSON, nullable=False)

    @declared_attr
    def result(cls):
        return Column(Float, nullable=True)

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def user(cls):
        return relationship("User", back_populates="calculations")

    @classmethod
    def create(cls, calculation_type: str, user_id: uuid.UUID, inputs: List[float]) -> "Calculation":
        """Factory: return the right subclass for the given calculation_type."""
        classes = {
            "addition":       Addition,
            "subtraction":    Subtraction,
            "multiplication": Multiplication,
            "division":       Division,
        }
        klass = classes.get(calculation_type.lower())
        if not klass:
            raise ValueError(f"Unsupported calculation type: {calculation_type}")
        return klass(user_id=user_id, inputs=inputs)

    def get_result(self) -> float:
        raise NotImplementedError

    def __repr__(self):
        return f"<Calculation(type={self.type}, inputs={self.inputs})>"


class Calculation(Base, AbstractCalculation):
    __mapper_args__ = {
        "polymorphic_on":       "type",
        "polymorphic_identity": "calculation",
    }


class Addition(Calculation):
    __mapper_args__ = {"polymorphic_identity": "addition"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("At least two numbers are required.")
        return sum(float(x) for x in self.inputs)


class Subtraction(Calculation):
    __mapper_args__ = {"polymorphic_identity": "subtraction"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("At least two numbers are required.")
        result = float(self.inputs[0])
        for v in self.inputs[1:]:
            result -= float(v)
        return result


class Multiplication(Calculation):
    __mapper_args__ = {"polymorphic_identity": "multiplication"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("At least two numbers are required.")
        result = 1.0
        for v in self.inputs:
            result *= float(v)
        return result


class Division(Calculation):
    __mapper_args__ = {"polymorphic_identity": "division"}

    def get_result(self) -> float:
        if not isinstance(self.inputs, list):
            raise ValueError("Inputs must be a list of numbers.")
        if len(self.inputs) < 2:
            raise ValueError("At least two numbers are required.")
        result = float(self.inputs[0])
        for v in self.inputs[1:]:
            if float(v) == 0:
                raise ValueError("Cannot divide by zero.")
            result /= float(v)
        return result
