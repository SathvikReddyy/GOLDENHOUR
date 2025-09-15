import sys
import os
from pymongo import MongoClient
from db import Database
from dotenv import load_dotenv

def test_connection():
    """Test MongoDB connection"""
    try:
        # Try direct connection first
        print("\n=== Testing direct MongoDB connection ===")
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.server_info()  # Will raise an exception if connection fails
        print("✅ Direct MongoDB connection successful")
        
        # List all databases
        print("\nAvailable databases:")
        for db_name in client.list_database_names():
            print(f"- {db_name}")
            
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB directly: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure MongoDB is installed and running")
        print("   - On Windows: Run 'net start MongoDB' in an administrator command prompt")
        print("   - On macOS: Run 'brew services start mongodb-community'")
        print("   - On Linux: Run 'sudo systemctl start mongod'")
        print("2. Check if MongoDB is running on the default port (27017)")
        print("3. Verify your MongoDB connection string in the .env file")
        return False
    
    return True

def test_database_class():
    """Test the Database class"""
    print("\n=== Testing Database class ===")
    db = Database()
    
    # Test user creation
    user_data = {
        'name': 'Test User',
        'email': 'test@example.com',
        'phone': '+1234567890',
        'password_hash': 'hashed_password',
        'address': '123 Test St'
    }
    
    print("\nTesting user creation...")
    success, message, user_id = db.create_user(user_data)
    if success:
        print(f"✅ User created successfully with ID: {user_id}")
    else:
        print(f"❌ Failed to create user: {message}")
    
    # Test driver creation
    driver_data = {
        'name': 'Test Driver',
        'email': 'driver@example.com',
        'phone': '+1987654321',
        'password_hash': 'hashed_password',
        'vehicle': {
            'type': 'car',
            'model': 'Test Model',
            'license_plate': 'TEST123'
        },
        'location': {
            'type': 'Point',
            'coordinates': [72.8777, 19.0760]  # Mumbai coordinates
        },
        'is_available': True
    }
    
    print("\nTesting driver creation...")
    success, message, driver_id = db.create_driver(driver_data)
    if success:
        print(f"✅ Driver created successfully with ID: {driver_id}")
    else:
        print(f"❌ Failed to create driver: {message}")
    
    # Close the connection
    db.close_connection()

def main():
    print("=== MongoDB Database Tester ===")
    
    # Check if MongoDB is running and accessible
    if not test_connection():
        sys.exit(1)
    
    # Test the Database class
    test_database_class()
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()
