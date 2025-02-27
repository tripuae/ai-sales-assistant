from database_schema import PriceDatabase
from data_loader import create_database

def main():
    print("TripUAE Sales Assistant - Simple Test")
    # Create price database
    price_db = create_database()
    print("Database loaded successfully!")
    print(f"Available tours: {list(price_db.tours.keys())}")
    
if __name__ == "__main__":
    main()