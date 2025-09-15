from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError, PyMongoError
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Database:
    def __init__(self, connection_string=None, db_name=None):
        """
        Initialize database connection
        If no parameters are provided, uses environment variables
        """
        self.connection_string = connection_string or os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.db_name = db_name or os.getenv('DB_NAME', 'goldenhour')
        self.client = None
        self.db = None
        self.connect()
        self._create_indexes()

    def connect(self):
        """Establish connection to MongoDB"""
        try:
            print(f"Attempting to connect to MongoDB at: {self.connection_string}")
            print(f"Using database: {self.db_name}")
            
            # Set a server selection timeout (in milliseconds)
            self.client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=30000,         # 30 second connection timeout
                socketTimeoutMS=30000           # 30 second socket timeout
            )
            
            # Test the connection
            self.client.server_info()  # Will raise an exception if connection fails
            self.db = self.client[self.db_name]
            
            # Test if we can access the database
            self.db.command('ping')
            print("✅ Successfully connected to MongoDB")
            return True
            
        except Exception as e:
            print("❌ Failed to connect to MongoDB:")
            print(f"Error details: {str(e)}")
            print("\nTroubleshooting steps:")
            print("1. Make sure MongoDB is running locally or the connection string is correct")
            print("2. Check if the MongoDB service is started")
            print("3. Verify the connection string in .env file")
            print(f"Current connection string: {self.connection_string}")
            self.client = None
            self.db = None
            return False

    def _create_indexes(self):
        """Create necessary indexes for collections"""
        if self.db is not None:
            try:
                # User collection indexes
                self.db.users.create_index([("email", ASCENDING)], unique=True)
                self.db.users.create_index([("phone", ASCENDING)], unique=True, sparse=True)
                
                # Driver collection indexes
                self.db.drivers.create_index([("email", ASCENDING)], unique=True)
                self.db.drivers.create_index([("phone", ASCENDING)], unique=True, sparse=True)
                self.db.drivers.create_index([("location", "2dsphere")])
                print("Database indexes created successfully")
            except Exception as e:
                print(f"Error creating database indexes: {e}")

    # User Management Methods
    def create_user(self, user_data):
        """
        Create a new user
        :param user_data: Dictionary containing user details
        :return: (success: bool, message: str, user_id: str)
        """
        if self.db is None:
            return False, "Database connection not established", None
            
        try:
            print(f"Attempting to create user with data: {user_data}")
            
            # Add timestamps
            current_time = datetime.utcnow()
            user_data['created_at'] = current_time
            user_data['updated_at'] = current_time
            
            # Insert the document
            result = self.db.users.insert_one(user_data)
            
            if result.inserted_id:
                user_id = str(result.inserted_id)
                print(f"✅ Successfully created user with ID: {user_id}")
                return True, "User created successfully", user_id
            else:
                return False, "Failed to create user: No ID returned", None
                
        except DuplicateKeyError as e:
            error_msg = f"User with this email or phone already exists: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg, None
            
        except Exception as e:
            error_msg = f"Error creating user: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, None

    def get_user(self, user_id=None, email=None, phone=None):
        """
        Get user by ID, email, or phone
        :return: User document or None if not found
        """
        query = {}
        if user_id:
            query['_id'] = ObjectId(user_id)
        elif email:
            query['email'] = email
        elif phone:
            query['phone'] = phone
        else:
            return None

        try:
            user = self.db.users.find_one(query)
            if user:
                user['_id'] = str(user['_id'])  # Convert ObjectId to string
            return user
        except PyMongoError as e:
            print(f"Database error: {e}")
            return None

    def update_user(self, user_id, update_data):
        """
        Update user information
        :return: True if successful, False otherwise
        """
        try:
            update_data['updated_at'] = datetime.utcnow()
            result = self.db.users.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"Database error: {e}")
            return False

    # Driver Management Methods
    def create_driver(self, driver_data):
        """
        Create a new driver
        :param driver_data: Dictionary containing driver details
        :return: (success: bool, message: str, driver_id: str)
        """
        if self.db is None:
            return False, "Database connection not established", None
            
        try:
            print(f"Attempting to create driver with data: {driver_data}")
            
            # Add timestamps and default values
            current_time = datetime.utcnow()
            driver_data['created_at'] = current_time
            driver_data['updated_at'] = current_time
            driver_data['is_available'] = driver_data.get('is_available', True)
            
            # Ensure location is in proper GeoJSON format if provided
            if 'location' in driver_data and isinstance(driver_data['location'], dict):
                if 'type' not in driver_data['location']:
                    driver_data['location']['type'] = 'Point'
                if 'coordinates' not in driver_data['location']:
                    return False, "Location must include 'coordinates' as [longitude, latitude]", None
            
            # Insert the document
            result = self.db.drivers.insert_one(driver_data)
            
            if result.inserted_id:
                driver_id = str(result.inserted_id)
                print(f"✅ Successfully created driver with ID: {driver_id}")
                return True, "Driver created successfully", driver_id
            else:
                return False, "Failed to create driver: No ID returned", None
                
        except DuplicateKeyError as e:
            error_msg = f"Driver with this email or phone already exists: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg, None
            
        except Exception as e:
            error_msg = f"Error creating driver: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, None

    def get_driver(self, driver_id=None, email=None, phone=None):
        """
        Get driver by ID, email, or phone
        :return: Driver document or None if not found
        """
        query = {}
        if driver_id:
            query['_id'] = ObjectId(driver_id)
        elif email:
            query['email'] = email
        elif phone:
            query['phone'] = phone
        else:
            return None

        try:
            driver = self.db.drivers.find_one(query)
            if driver:
                driver['_id'] = str(driver['_id'])  # Convert ObjectId to string
            return driver
        except PyMongoError as e:
            print(f"Database error: {e}")
            return None

    def update_driver_location(self, driver_id, location):
        """
        Update driver's current location
        :param driver_id: Driver's ID
        :param location: GeoJSON point {type: "Point", coordinates: [longitude, latitude]}
        :return: True if successful, False otherwise
        """
        try:
            result = self.db.drivers.update_one(
                {'_id': ObjectId(driver_id)},
                {
                    '$set': {
                        'location': location,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"Database error: {e}")
            return False

    def find_nearby_drivers(self, location, max_distance=5000, limit=10):
        """
        Find drivers within a certain distance from a location
        :param location: GeoJSON point {type: "Point", coordinates: [longitude, latitude]}
        :param max_distance: Maximum distance in meters
        :param limit: Maximum number of drivers to return
        :return: List of nearby drivers
        """
        try:
            nearby_drivers = self.db.drivers.find({
                'location': {
                    '$near': {
                        '$geometry': location,
                        '$maxDistance': max_distance
                    }
                },
                'is_available': True
            }).limit(limit)

            return list(nearby_drivers)
        except PyMongoError as e:
            print(f"Database error: {e}")
            return []

    def close_connection(self):
        """Close the MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")

# Create a global database instance
db = Database()

# Example usage:
if __name__ == "__main__":
    # Example user data
    user_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+1234567890',
        'password_hash': 'hashed_password_here',
        'address': '123 Main St'
    }
    
    # Example driver data
    driver_data = {
        'name': 'Jane Smith',
        'email': 'jane@example.com',
        'phone': '+1987654321',
        'password_hash': 'hashed_password_here',
        'vehicle': {
            'type': 'car',
            'model': 'Toyota Camry',
            'license_plate': 'ABC123'
        },
        'location': {
            'type': 'Point',
            'coordinates': [-73.856077, 40.848447]  # [longitude, latitude]
        },
        'is_available': True
    }
    
    try:
        # Initialize database
        db = Database()
        
        # Create user and driver
        user_id = db.create_user(user_data)
        driver_id = db.create_driver(driver_data)
        
        print(f"Created user with ID: {user_id}")
        print(f"Created driver with ID: {driver_id}")
        
        # Find nearby drivers
        location = {
            'type': 'Point',
            'coordinates': [-73.856077, 40.848447]
        }
        nearby = db.find_nearby_drivers(location)
        print(f"Found {len(nearby)} nearby drivers")
        
    finally:
        # Close the connection when done
        db.close_connection()