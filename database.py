"""
MongoDB Database Module for GitLab MR Manager
Handles database connection, collections, and basic CRUD operations
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """MongoDB database manager for GitLab MR Manager"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collections = {}
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            # Get MongoDB configuration from environment variables
            mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
            db_name = os.getenv('MONGO_DB_NAME', 'gitlab_mr_manager')
            
            # Connection options
            connection_options = {
                'serverSelectionTimeoutMS': 5000,  # 5 seconds timeout
                'connectTimeoutMS': 10000,         # 10 seconds connection timeout
                'socketTimeoutMS': 10000,          # 10 seconds socket timeout
            }
            
            # Add authentication if provided
            mongo_user = os.getenv('MONGO_USER')
            mongo_password = os.getenv('MONGO_PASSWORD')
            
            if mongo_user and mongo_password:
                # If using MongoDB Atlas or authenticated MongoDB
                if 'mongodb+srv://' in mongo_uri:
                    # MongoDB Atlas connection string
                    mongo_uri = f"mongodb+srv://{mongo_user}:{mongo_password}@{mongo_uri.split('@')[1]}"
                else:
                    # Local MongoDB with authentication
                    mongo_uri = f"mongodb://{mongo_user}:{mongo_password}@{mongo_uri.split('://')[1]}"
            
            logger.info(f"Connecting to MongoDB: {mongo_uri}")
            self.client = MongoClient(mongo_uri, **connection_options)
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("MongoDB connection successful")
            
            # Get database
            self.db = self.client[db_name]
            
            # Initialize collections
            self._init_collections()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection failed: {e}")
            self.client = None
            self.db = None
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            self.client = None
            self.db = None
    
    def _init_collections(self):
        """Initialize database collections"""
        if self.db is None:
            return
            
        # Define collections for different modules
        self.collections = {
            'users': self.db.users,
            'merge_requests': self.db.merge_requests,
            'activities': self.db.activities,
            'settings': self.db.settings,
            'notifications': self.db.notifications,
            'analytics': self.db.analytics,
            'cache': self.db.cache
        }
        
        # Create indexes for better performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users collection indexes
            if 'users' in self.collections:
                self.collections['users'].create_index([("username", 1)], unique=True)
                self.collections['users'].create_index([("email", 1)], unique=True)
            
            # Merge requests collection indexes
            if 'merge_requests' in self.collections:
                self.collections['merge_requests'].create_index([("mr_id", 1)], unique=True)
                self.collections['merge_requests'].create_index([("author", 1)])
                self.collections['merge_requests'].create_index([("state", 1)])
                self.collections['merge_requests'].create_index([("created_at", -1)])
                self.collections['merge_requests'].create_index([("labels", 1)])
            
            # Activities collection indexes
            if 'activities' in self.collections:
                self.collections['activities'].create_index([("user_id", 1)])
                self.collections['activities'].create_index([("activity_type", 1)])
                self.collections['activities'].create_index([("timestamp", -1)])
            
            # Settings collection indexes
            if 'settings' in self.collections:
                self.collections['settings'].create_index([("key", 1)], unique=True)
            
            # Notifications collection indexes
            if 'notifications' in self.collections:
                self.collections['notifications'].create_index([("user_id", 1)])
                self.collections['notifications'].create_index([("read", 1)])
                self.collections['notifications'].create_index([("created_at", -1)])
            
            # Analytics collection indexes
            if 'analytics' in self.collections:
                self.collections['analytics'].create_index([("date", 1)])
                self.collections['analytics'].create_index([("metric_type", 1)])
            
            # Cache collection indexes
            if 'cache' in self.collections:
                self.collections['cache'].create_index([("key", 1)], unique=True)
                self.collections['cache'].create_index([("expires_at", 1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def is_connected(self):
        """Check if database is connected"""
        try:
            if self.client is not None:
                self.client.admin.command('ping')
                return True
            return False
        except:
            return False
    
    def get_collection(self, collection_name):
        """Get a specific collection"""
        return self.collections.get(collection_name)
    
    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

# Global database instance
db_manager = DatabaseManager()

# Collection access functions
def get_users_collection():
    """Get users collection"""
    return db_manager.get_collection('users')

def get_mrs_collection():
    """Get merge requests collection"""
    return db_manager.get_collection('merge_requests')

def get_activities_collection():
    """Get activities collection"""
    return db_manager.get_collection('activities')

def get_settings_collection():
    """Get settings collection"""
    return db_manager.get_collection('settings')

def get_notifications_collection():
    """Get notifications collection"""
    return db_manager.get_collection('notifications')

def get_analytics_collection():
    """Get analytics collection"""
    return db_manager.get_collection('analytics')

def get_cache_collection():
    """Get cache collection"""
    return db_manager.get_collection('cache')

# Basic CRUD operations
def insert_document(collection_name, document):
    """Insert a document into a collection"""
    try:
        collection = db_manager.get_collection(collection_name)
        if collection is not None:
            document['created_at'] = datetime.utcnow()
            result = collection.insert_one(document)
            logger.info(f"Document inserted into {collection_name}: {result.inserted_id}")
            return result.inserted_id
        return None
    except Exception as e:
        logger.error(f"Error inserting document into {collection_name}: {e}")
        return None

def find_documents(collection_name, query=None, limit=None, sort=None):
    """Find documents in a collection"""
    try:
        collection = db_manager.get_collection(collection_name)
        if collection is not None:
            cursor = collection.find(query or {})
            if sort:
                cursor = cursor.sort(sort)
            if limit:
                cursor = cursor.limit(limit)
            return list(cursor)
        return []
    except Exception as e:
        logger.error(f"Error finding documents in {collection_name}: {e}")
        return []

def find_one_document(collection_name, query):
    """Find one document in a collection"""
    try:
        collection = db_manager.get_collection(collection_name)
        if collection is not None:
            return collection.find_one(query)
        return None
    except Exception as e:
        logger.error(f"Error finding document in {collection_name}: {e}")
        return None

def update_document(collection_name, query, update_data):
    """Update a document in a collection"""
    try:
        collection = db_manager.get_collection(collection_name)
        if collection is not None:
            update_data['updated_at'] = datetime.utcnow()
            result = collection.update_one(query, {'$set': update_data})
            logger.info(f"Document updated in {collection_name}: {result.modified_count} modified")
            return result.modified_count > 0
        return False
    except Exception as e:
        logger.error(f"Error updating document in {collection_name}: {e}")
        return False

def delete_document(collection_name, query):
    """Delete a document from a collection"""
    try:
        collection = db_manager.get_collection(collection_name)
        if collection is not None:
            result = collection.delete_one(query)
            logger.info(f"Document deleted from {collection_name}: {result.deleted_count} deleted")
            return result.deleted_count > 0
        return False
    except Exception as e:
        logger.error(f"Error deleting document from {collection_name}: {e}")
        return False

def count_documents(collection_name, query=None):
    """Count documents in a collection"""
    try:
        collection = db_manager.get_collection(collection_name)
        if collection is not None:
            return collection.count_documents(query or {})
        return 0
    except Exception as e:
        logger.error(f"Error counting documents in {collection_name}: {e}")
        return 0
