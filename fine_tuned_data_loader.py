"""
Fine‑tuned Data Loader for TripUAE Tourism Pricing System.
This version loads all tour and transfer data from an external JSON file,
validates it using Pydantic, and returns a PriceDatabase object.
"""

import json
import logging
from pathlib import Path
from database_schema import PriceDatabase  # Assumes PriceDatabase is a Pydantic model

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_pricing_data_from_json(filepath: str) -> PriceDatabase:
    """
    Load pricing data from an external JSON file and return a PriceDatabase object.
    This decouples data from code and makes updates easier.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        logger.info("Pricing data loaded successfully from %s", filepath)
        
        # Use Pydantic's parse_obj to validate and build the database.
        db = PriceDatabase.parse_obj(raw_data)
        logger.info("PriceDatabase created successfully")
        return db
    except Exception as e:
        logger.error("Error loading pricing data: %s", e)
        raise

if __name__ == "__main__":
    # Adjust the path to your JSON file as needed.
    data_file = Path(__file__).parent / "pricing_data.json"
    db = load_pricing_data_from_json(str(data_file))
    print(db.json(indent=2))