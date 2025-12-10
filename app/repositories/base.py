"""
Base repository class with common CRUD operations.

Provides generic database operations that can be inherited
by specific repositories.
"""

from typing import Optional, List, Dict, Any, TypeVar, Generic
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Base repository with common CRUD operations.

    Generic repository that provides standard database operations
    for MongoDB collections.
    """

    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str):
        """
        Initialize repository.

        Args:
            database: MongoDB database instance
            collection_name: Name of the collection
        """
        self.db = database
        self.collection = database[collection_name]

    async def create(self, document: Dict[str, Any]) -> str:
        """
        Create a new document.

        Args:
            document: Document data to insert

        Returns:
            ID of created document
        """
        document["created_at"] = datetime.utcnow()
        document["updated_at"] = datetime.utcnow()

        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document dict or None if not found
        """
        try:
            document = await self.collection.find_one({"_id": ObjectId(doc_id)})
            if document:
                document["_id"] = str(document["_id"])
            return document
        except Exception:
            return None

    async def get_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        Get document by specific field value.

        Args:
            field: Field name
            value: Field value to search for

        Returns:
            Document dict or None if not found
        """
        document = await self.collection.find_one({field: value})
        if document:
            document["_id"] = str(document["_id"])
        return document

    async def find_many(
        self,
        filter_dict: Dict[str, Any] = None,
        skip: int = 0,
        limit: int = 100,
        sort: List[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Find multiple documents with pagination.

        Args:
            filter_dict: MongoDB filter query
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort: List of (field, direction) tuples for sorting

        Returns:
            List of matching documents
        """
        filter_dict = filter_dict or {}

        cursor = self.collection.find(filter_dict).skip(skip).limit(limit)

        if sort:
            cursor = cursor.sort(sort)

        documents = await cursor.to_list(length=limit)

        for doc in documents:
            doc["_id"] = str(doc["_id"])

        return documents

    async def update(self, doc_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update document by ID.

        Args:
            doc_id: Document ID
            update_data: Fields to update

        Returns:
            True if updated, False otherwise
        """
        try:
            update_data["updated_at"] = datetime.utcnow()

            result = await self.collection.update_one(
                {"_id": ObjectId(doc_id)},
                {"$set": update_data}
            )

            return result.modified_count > 0
        except Exception:
            return False

    async def delete(self, doc_id: str) -> bool:
        """
        Delete document by ID.

        Args:
            doc_id: Document ID

        Returns:
            True if deleted, False otherwise
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(doc_id)})
            return result.deleted_count > 0
        except Exception:
            return False

    async def count(self, filter_dict: Dict[str, Any] = None) -> int:
        """
        Count documents matching filter.

        Args:
            filter_dict: MongoDB filter query

        Returns:
            Number of matching documents
        """
        filter_dict = filter_dict or {}
        return await self.collection.count_documents(filter_dict)

    async def exists(self, filter_dict: Dict[str, Any]) -> bool:
        """
        Check if any document matches the filter.

        Args:
            filter_dict: MongoDB filter query

        Returns:
            True if at least one document exists
        """
        count = await self.collection.count_documents(filter_dict, limit=1)
        return count > 0
