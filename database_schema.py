"""
Database schema for TripUAE tourism pricing system.
This module defines the data structures for storing and retrieving tour pricing information.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator

class PriceOption(BaseModel):
    """Price option for a specific tour variant and location."""
    adult_price: float = Field(..., ge=0, description="Price for adult tickets (must be non-negative).")
    child_price: Optional[float] = Field(None, ge=0, description="Price for child tickets (if applicable).")
    child_age_min: Optional[int] = Field(None, ge=0, description="Minimum age for child pricing.")
    child_age_max: Optional[int] = Field(None, ge=0, description="Maximum age for child pricing.")
    infant_price: Optional[float] = Field(0.0, ge=0, description="Price for infant tickets (default is 0).")
    infant_age_max: Optional[int] = Field(3, ge=0, description="Maximum age for infant free tickets.")
    notes: Optional[str] = Field(None, description="Additional notes for this price option.")

    @validator("child_age_max")
    def check_child_age(cls, v, values):
        min_age = values.get("child_age_min")
        if min_age is not None and v is not None and v <= min_age:
            raise ValueError("child_age_max must be greater than child_age_min")
        return v

class TourVariant(BaseModel):
    """Variant of a tour (e.g., standard, premium, VIP)."""
    name: str = Field(..., description="Name of the tour variant.")
    description: str = Field(..., description="Description of the tour variant.")
    duration: str = Field(..., description="Duration of the tour variant.")
    pricing: Dict[str, PriceOption] = Field(..., description="Pricing details by emirate (e.g., 'dubai', 'abu_dhabi').")
    includes_transfer: bool = Field(False, description="Indicates whether transfer is included.")
    includes_meals: bool = Field(False, description="Indicates whether meals are included.")
    available_days: List[str] = Field(default_factory=lambda: ["daily"], description="Days when the tour is available.")
    departure_times: Optional[List[str]] = Field(None, description="Optional list of departure times.")
    min_participants: int = Field(1, ge=1, description="Minimum number of participants required.")
    notes: Optional[str] = Field(None, description="Additional notes about the tour variant.")

class TourPackage(BaseModel):
    """Complete tour package with all variants and additional information."""
    id: str = Field(..., description="Unique identifier for the tour package.")
    name: str = Field(..., description="Name of the tour package.")
    type: str = Field(..., description="Type of tour (e.g., excursion, ticket, cruise).")
    description: str = Field(..., description="Full description of the tour package.")
    location: str = Field(..., description="Location of the tour.")
    variants: Dict[str, TourVariant] = Field(..., description="Available variants for this tour package.")
    upsell_suggestions: List[str] = Field(default_factory=list, description="List of upsell suggestions.")
    image_urls: Optional[List[str]] = Field(None, description="Optional list of image URLs for the tour.")

class TransferOption(BaseModel):
    """Transfer pricing between locations."""
    from_location: str = Field(..., description="Origin location for the transfer.")
    to_location: str = Field(..., description="Destination location for the transfer.")
    passenger_range: str = Field(..., description="Passenger range (e.g., '1-7').")
    duration: str = Field(..., description="Duration of the transfer service.")
    price_usd: float = Field(..., ge=0, description="Price in USD (must be non-negative).")

class PriceDatabase(BaseModel):
    """Complete price database for all tours and transfers."""
    tours: Dict[str, TourPackage] = Field(..., description="Dictionary of tour packages.")
    transfers: List[TransferOption] = Field(..., description="List of available transfer options.")