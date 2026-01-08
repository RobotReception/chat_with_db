"""
Query Cache - Temporary storage for query results
Stores query results with query_id for later retrieval (Excel export, full data view)
"""
import uuid
import time
from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class QueryCache:
    """In-memory cache for query results with TTL"""
    
    def __init__(self, ttl_hours: int = 1):
        """
        Initialize query cache
        
        Args:
            ttl_hours: Time to live in hours (default: 1 hour)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_hours = ttl_hours
        self._cleanup_interval = 300  # Cleanup every 5 minutes
        self._last_cleanup = time.time()
    
    def _generate_query_id(self) -> str:
        """Generate unique query ID"""
        return str(uuid.uuid4())
    
    def store(
        self,
        data: List[Dict],
        question: str,
        sql_query: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store query results in cache
        
        Args:
            data: Query results (list of dicts)
            question: Original user question
            sql_query: SQL query executed
            metadata: Optional metadata
        
        Returns:
            query_id: Unique identifier for this query
        """
        query_id = self._generate_query_id()
        expires_at = datetime.now() + timedelta(hours=self.ttl_hours)
        
        self._cache[query_id] = {
            "data": data,
            "question": question,
            "sql_query": sql_query,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "expires_at": expires_at.isoformat(),
            "row_count": len(data)
        }
        
        logger.info(
            f"Query cached",
            extra={
                "query_id": query_id,
                "row_count": len(data),
                "expires_at": expires_at.isoformat()
            }
        )
        
        # Periodic cleanup
        self._cleanup_expired()
        
        return query_id
    
    def get(self, query_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve query results from cache
        
        Args:
            query_id: Query identifier
        
        Returns:
            Cached data or None if not found/expired
        """
        if query_id not in self._cache:
            return None
        
        entry = self._cache[query_id]
        
        # Check expiration
        expires_at = datetime.fromisoformat(entry["expires_at"])
        if datetime.now() > expires_at:
            del self._cache[query_id]
            logger.info(f"Query expired and removed: {query_id}")
            return None
        
        return entry
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        
        self._last_cleanup = now
        now_dt = datetime.now()
        
        expired_ids = [
            qid for qid, entry in self._cache.items()
            if datetime.fromisoformat(entry["expires_at"]) < now_dt
        ]
        
        for qid in expired_ids:
            del self._cache[qid]
        
        if expired_ids:
            logger.info(f"Cleaned up {len(expired_ids)} expired queries")
    
    def delete(self, query_id: str) -> bool:
        """
        Manually delete a cached query
        
        Args:
            query_id: Query identifier
        
        Returns:
            True if deleted, False if not found
        """
        if query_id in self._cache:
            del self._cache[query_id]
            logger.info(f"Query manually deleted: {query_id}")
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self._cleanup_expired()
        return {
            "total_queries": len(self._cache),
            "ttl_hours": self.ttl_hours
        }


# Global cache instance
query_cache = QueryCache(ttl_hours=1)
