# -*- coding: utf-8 -*-
"""
Cache management system for Sky Globe application.
Provides memory-based caching with TTL support and Streamlit cache integration.
"""

import time
import streamlit as st
from typing import Any, Optional, Dict, Tuple
from datetime import datetime, timedelta
import json
import hashlib
import logging

from src.utils.config import config


class CacheManager:
    """
    Memory-based cache manager with TTL (Time To Live) support.
    Provides efficient caching for API responses and computed data.
    """
    
    def __init__(self):
        """Initialize cache manager."""
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl_config = {
            'weather': config.get_cache_ttl('weather'),      # 10 minutes default
            'geocoding': config.get_cache_ttl('geocoding'),  # 1 hour default
            'cities': 86400,                          # 24 hours
            'default': 300                            # 5 minutes
        }
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a unique cache key from arguments.
        
        Args:
            prefix: Cache key prefix (e.g., 'weather', 'geocoding')
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Unique cache key string
        """
        # Create a consistent string representation
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        
        # Generate hash for consistent key length
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{prefix}:{key_hash}"
    
    def _is_expired(self, timestamp: float, cache_type: str = 'default') -> bool:
        """
        Check if cache entry is expired.
        
        Args:
            timestamp: Cache entry timestamp
            cache_type: Type of cache entry for TTL lookup
            
        Returns:
            True if expired, False otherwise
        """
        ttl = self.ttl_config.get(cache_type, self.ttl_config['default'])
        return time.time() - timestamp > ttl
    
    def get(self, cache_type: str, *args, **kwargs) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            cache_type: Type of cache entry
            *args: Arguments for key generation
            **kwargs: Keyword arguments for key generation
            
        Returns:
            Cached value or None if not found/expired
        """
        key = self._generate_key(cache_type, *args, **kwargs)
        
        if key in self.cache:
            data, timestamp = self.cache[key]
            
            if not self._is_expired(timestamp, cache_type):
                self.stats['hits'] += 1
                self.logger.debug(f"Cache hit for key: {cache_type}")
                return data
            else:
                # Remove expired entry
                del self.cache[key]
                self.stats['evictions'] += 1
                self.logger.debug(f"Cache expired for key: {cache_type}")
        
        self.stats['misses'] += 1
        return None
    
    def set(self, cache_type: str, value: Any, *args, **kwargs) -> None:
        """
        Set value in cache.
        
        Args:
            cache_type: Type of cache entry
            value: Value to cache
            *args: Arguments for key generation
            **kwargs: Keyword arguments for key generation
        """
        key = self._generate_key(cache_type, *args, **kwargs)
        self.cache[key] = (value, time.time())
        self.stats['sets'] += 1
        self.logger.debug(f"Cache set for key: {cache_type}")
    
    def delete(self, cache_type: str, *args, **kwargs) -> bool:
        """
        Delete specific cache entry.
        
        Args:
            cache_type: Type of cache entry
            *args: Arguments for key generation
            **kwargs: Keyword arguments for key generation
            
        Returns:
            True if entry was deleted, False if not found
        """
        key = self._generate_key(cache_type, *args, **kwargs)
        
        if key in self.cache:
            del self.cache[key]
            self.logger.debug(f"Cache entry deleted: {cache_type}")
            return True
        return False
    
    def clear_by_type(self, cache_type: str) -> int:
        """
        Clear all cache entries of a specific type.
        
        Args:
            cache_type: Type of cache entries to clear
            
        Returns:
            Number of entries cleared
        """
        prefix = f"{cache_type}:"
        keys_to_delete = [key for key in self.cache.keys() if key.startswith(prefix)]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        self.logger.info(f"Cleared {len(keys_to_delete)} entries of type: {cache_type}")
        return len(keys_to_delete)
    
    def clear_all(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        count = len(self.cache)
        self.cache.clear()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
        self.logger.info(f"Cache cleared: {count} entries removed")
        return count
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = []
        
        for key, (data, timestamp) in self.cache.items():
            cache_type = key.split(':', 1)[0]
            if self._is_expired(timestamp, cache_type):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        self.stats['evictions'] += len(expired_keys)
        self.logger.info(f"Cleaned up {len(expired_keys)} expired entries")
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_entries': len(self.cache),
            'total_requests': total_requests,
            'cache_hits': self.stats['hits'],
            'cache_misses': self.stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'cache_sets': self.stats['sets'],
            'evictions': self.stats['evictions'],
            'ttl_config': self.ttl_config.copy()
        }
    
    def get_size_info(self) -> Dict[str, int]:
        """
        Get cache size information by type.
        
        Returns:
            Dictionary with size info by cache type
        """
        type_counts = {}
        
        for key in self.cache.keys():
            cache_type = key.split(':', 1)[0]
            type_counts[cache_type] = type_counts.get(cache_type, 0) + 1
        
        return type_counts


# Singleton instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get singleton cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


# Streamlit cache decorators for specific functions
@st.cache_data(ttl=config.get_cache_ttl('weather'), show_spinner=False)
def cached_weather_data(city_name: str, country_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Streamlit cached function for weather data.
    This is a placeholder - actual implementation will be in weather service.
    
    Args:
        city_name: City name
        country_code: Optional country code
        
    Returns:
        Weather data or None
    """
    # This will be implemented in weather_service.py
    return None


@st.cache_data(ttl=config.get_cache_ttl('geocoding'), show_spinner=False)
def cached_geocoding_data(query: str) -> Optional[list]:
    """
    Streamlit cached function for geocoding data.
    This is a placeholder - actual implementation will be in geo service.
    
    Args:
        query: Search query
        
    Returns:
        Geocoding results or None
    """
    # This will be implemented in geo_service.py
    return None


@st.cache_data(ttl=86400, show_spinner=False)  # Cache for 24 hours
def cached_cities_data() -> Optional[Any]:
    """
    Streamlit cached function for cities data.
    This is a placeholder - actual implementation will be in geo service.
    
    Returns:
        Cities dataframe or None
    """
    # This will be implemented in geo_service.py
    return None


# Cache utilities
def invalidate_weather_cache():
    """Invalidate all weather-related caches."""
    cache_manager = get_cache_manager()
    cache_manager.clear_by_type('weather')
    
    # Clear Streamlit cache for weather data
    if hasattr(st, 'cache_data'):
        cached_weather_data.clear()


def invalidate_geocoding_cache():
    """Invalidate all geocoding-related caches."""
    cache_manager = get_cache_manager()
    cache_manager.clear_by_type('geocoding')
    
    # Clear Streamlit cache for geocoding data
    if hasattr(st, 'cache_data'):
        cached_geocoding_data.clear()


def get_cache_info() -> Dict[str, Any]:
    """
    Get comprehensive cache information for debugging.
    
    Returns:
        Dictionary with cache information
    """
    cache_manager = get_cache_manager()
    
    return {
        'memory_cache': cache_manager.get_stats(),
        'size_by_type': cache_manager.get_size_info(),
        'streamlit_cache_enabled': hasattr(st, 'cache_data'),
        'config': {
            'weather_ttl': config.get_cache_ttl('weather'),
            'geocoding_ttl': config.get_cache_ttl('geocoding')
        }
    }


def cleanup_all_caches():
    """Clean up all expired cache entries."""
    cache_manager = get_cache_manager()
    return cache_manager.cleanup_expired()