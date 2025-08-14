# -*- coding: utf-8 -*-
"""
Configuration management module for Sky Globe application.
Handles environment settings, API keys, and application constants.
"""

import os
import streamlit as st
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for Sky Globe application."""
    
    # Environment configurations
    ENVIRONMENTS = {
        'development': {
            'debug': True,
            'cache_ttl_weather': 60,  # 1 minute for development
            'cache_ttl_cities': 300,  # 5 minutes for development
            'log_level': 'DEBUG'
        },
        'production': {
            'debug': False,
            'cache_ttl_weather': 1800,  # 30 minutes for production
            'cache_ttl_cities': 3600,   # 1 hour for production
            'log_level': 'INFO'
        }
    }
    
    # Application constants
    MIN_SEARCH_LENGTH = 2
    MAX_SEARCH_RESULTS = 20
    DEFAULT_CONTINENT_FILTER = "すべて"
    DEFAULT_CITY = "Tokyo"
    
    # Map display settings
    MAP_DEFAULT_ZOOM = 2
    MAP_INITIAL_VIEW_STATE = {
        'latitude': 35.6762,
        'longitude': 139.6503,
        'zoom': MAP_DEFAULT_ZOOM,
        'pitch': 0,
        'bearing': 0
    }
    
    # Weather API settings
    WEATHER_API_TIMEOUT = 10
    WEATHER_UNITS = "metric"  # metric, imperial, standard
    
    # Cache settings
    CACHE_SIZE_LIMIT = 1000  # Maximum number of cached items
    
    def __init__(self):
        """Initialize configuration with environment detection."""
        self.environment = self._detect_environment()
        self.config = self.ENVIRONMENTS[self.environment]
        self.data_dir = self._get_data_directory()
        self.api_keys = self._load_api_keys()
    
    def _detect_environment(self) -> str:
        """
        Detect current environment based on environment variables.
        
        Returns:
            Environment name ('development' or 'production')
        """
        env = os.getenv('ENVIRONMENT', 'development').lower()
        return env if env in self.ENVIRONMENTS else 'development'
    
    def _get_data_directory(self) -> Path:
        """
        Get data directory path.
        
        Returns:
            Path to data directory
        """
        # Check for custom data directory
        custom_data_dir = os.getenv('DATA_DIR')
        if custom_data_dir:
            return Path(custom_data_dir)
        
        # Default to data directory relative to project root
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent
        return project_root / 'data'
    
    def _load_api_keys(self) -> Dict[str, Optional[str]]:
        """
        Load API keys from environment variables or Streamlit secrets.
        
        Returns:
            Dictionary containing API keys
        """
        api_keys = {}
        
        # OpenWeatherMap API key
        api_keys['openweathermap'] = (
            os.getenv('OPENWEATHERMAP_API_KEY') or
            st.secrets.get('OPENWEATHERMAP_API_KEY') if 'OPENWEATHERMAP_API_KEY' in st.secrets else None
        )
        
        return api_keys
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def get_cities_csv_path(self) -> Path:
        """Get path to cities CSV file."""
        return self.data_dir / 'cities.csv'
    
    def get_countries_csv_path(self) -> Path:
        """Get path to countries CSV file."""
        return self.data_dir / 'countries.csv'
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get API key for specified service.
        
        Args:
            service: Service name (e.g., 'openweathermap')
            
        Returns:
            API key or None if not found
        """
        return self.api_keys.get(service)
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.get('debug', False)
    
    @property
    def cache_ttl_weather(self) -> int:
        """Get weather cache TTL."""
        return self.get('cache_ttl_weather', 300)
    
    def get_cache_ttl(self, cache_type: str) -> int:
        """
        Get cache TTL for specified type.
        
        Args:
            cache_type: Type of cache ('weather', 'cities')
            
        Returns:
            TTL in seconds
        """
        key = f'cache_ttl_{cache_type}'
        return self.get(key, 300)  # Default 5 minutes
    
    def get_log_level(self) -> str:
        """Get logging level."""
        return self.get('log_level', 'INFO')
    
    def validate_setup(self) -> Dict[str, bool]:
        """
        Validate application setup and return status.
        
        Returns:
            Dictionary with validation results
        """
        results = {}
        
        # Check data files
        results['cities_data'] = self.get_cities_csv_path().exists()
        results['countries_data'] = self.get_countries_csv_path().exists()
        
        # Check API keys
        results['weather_api'] = self.get_api_key('openweathermap') is not None
        
        # Check data directory
        results['data_directory'] = self.data_dir.exists()
        
        return results
    
    def get_missing_requirements(self) -> list[str]:
        """
        Get list of missing requirements.
        
        Returns:
            List of missing requirement descriptions
        """
        validation = self.validate_setup()
        missing = []
        
        if not validation['cities_data']:
            missing.append(f"Cities data file: {self.get_cities_csv_path()}")
        
        if not validation['weather_api']:
            missing.append("OpenWeatherMap API key (set OPENWEATHERMAP_API_KEY)")
        
        if not validation['data_directory']:
            missing.append(f"Data directory: {self.data_dir}")
        
        return missing


# Create global config instance
config = Config()