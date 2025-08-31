#!/usr/bin/env python3
"""
Test script for MongoDB connection and basic operations
"""

import os
from dotenv import load_dotenv
from database import db_manager, insert_document, find_documents, find_one_document, update_document, delete_document

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB Connection...")
    
    if db_manager.is_connected():
        print("✅ MongoDB connection successful!")
        print(f"📊 Available collections: {list(db_manager.collections.keys())}")
        return True
    else:
        print("❌ MongoDB connection failed!")
        print("💡 Make sure MongoDB is running and check your connection settings")
        return False

def test_basic_operations():
    """Test basic CRUD operations"""
    print("\n🧪 Testing Basic CRUD Operations...")
    
    # Test document
    test_doc = {
        'name': 'Test User',
        'email': 'test@example.com',
        'role': 'developer',
        'test': True
    }
    
    # Test insert
    print("📝 Testing insert...")
    doc_id = insert_document('users', test_doc)
    if doc_id:
        print(f"✅ Document inserted with ID: {doc_id}")
    else:
        print("❌ Insert failed")
        return False
    
    # Test find one
    print("🔍 Testing find one...")
    found_doc = find_one_document('users', {'_id': doc_id})
    if found_doc:
        print(f"✅ Document found: {found_doc['name']}")
    else:
        print("❌ Find one failed")
        return False
    
    # Test update
    print("✏️ Testing update...")
    update_success = update_document('users', {'_id': doc_id}, {'role': 'senior_developer'})
    if update_success:
        print("✅ Document updated successfully")
    else:
        print("❌ Update failed")
        return False
    
    # Test find all
    print("📋 Testing find all...")
    all_docs = find_documents('users', {'test': True})
    print(f"✅ Found {len(all_docs)} test documents")
    
    # Test delete
    print("🗑️ Testing delete...")
    delete_success = delete_document('users', {'_id': doc_id})
    if delete_success:
        print("✅ Document deleted successfully")
    else:
        print("❌ Delete failed")
        return False
    
    return True

def test_collections():
    """Test all collections"""
    print("\n📚 Testing Collections...")
    
    collections = [
        'users',
        'merge_requests', 
        'activities',
        'settings',
        'notifications',
        'analytics',
        'cache'
    ]
    
    for collection_name in collections:
        collection = db_manager.get_collection(collection_name)
        if collection is not None:
            count = collection.count_documents({})
            print(f"✅ {collection_name}: {count} documents")
        else:
            print(f"❌ {collection_name}: Collection not available")

def main():
    """Main test function"""
    print("🚀 MongoDB Test Suite")
    print("=" * 50)
    
    # Test connection
    if not test_mongodb_connection():
        print("\n❌ Cannot proceed without database connection")
        return
    
    # Test collections
    test_collections()
    
    # Test basic operations
    if test_basic_operations():
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed")
    
    print("\n📋 Database Status:")
    print(f"   Connected: {db_manager.is_connected()}")
    print(f"   Database: {db_manager.db.name if db_manager.db is not None else 'None'}")
    print(f"   Collections: {len(db_manager.collections)}")

if __name__ == "__main__":
    main()
