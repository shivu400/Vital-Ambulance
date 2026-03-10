"""Data utilities for the Gray Mobility Smart Ambulance system."""

from .generator import generate_ambulance_batch
from .validator import validate_vitals

__all__ = ["generate_ambulance_batch", "validate_vitals"]
