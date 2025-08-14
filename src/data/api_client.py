# -*- coding: utf-8 -*-
"""
API client for external weather and geocoding services.
Handles OpenWeatherMap API requests and response processing.
"""

import requests
import streamlit as st
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from src.utils.config import config


class APIError(Exception):
    """Custom exception for API errors."""
    pass


class RateLimitError(APIError):
    """Custom exception for rate limit errors."""
    pass


class APIClient:
    """
    Client for external API services (OpenWeatherMap).
    Handles authentication, rate limiting, and response processing.
    """
    
    def __init__(self):
        """Initialize API client."""
        self.logger = logging.getLogger(__name__)
        self.api_key = config.get_api_key('openweathermap')
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.geocoding_url = "https://api.openweathermap.org/geo/1.0"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        
        # Request statistics
        self.request_count = 0
        self.error_count = 0
        self.last_error = None
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Sky-Globe-App/1.0'
        })
    
    def _check_api_key(self) -> bool:
        """Check if API key is available."""
        if not self.api_key:
            st.error("OpenWeatherMap APIキーが設定されていません。")
            return False
        return True
    
    def _rate_limit(self):
        """Apply rate limiting."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to API with error handling.
        
        Args:
            url: Request URL
            params: Request parameters
            
        Returns:
            JSON response data or None if failed
        """
        if not self._check_api_key():
            return None
        
        # Add API key to parameters
        params['appid'] = self.api_key
        
        # Apply rate limiting
        self._rate_limit()
        
        try:
            self.request_count += 1
            
            response = self.session.get(
                url, 
                params=params, 
                timeout=config.WEATHER_API_TIMEOUT
            )
            
            # Handle different HTTP status codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                error_msg = "APIキーが無効です"
                self.logger.error(f"API authentication failed: {response.text}")
                raise APIError(error_msg)
            elif response.status_code == 429:
                error_msg = "API制限に達しました"
                self.logger.warning(f"Rate limit exceeded: {response.text}")
                raise RateLimitError(error_msg)
            elif response.status_code == 404:
                error_msg = "データが見つかりません"
                self.logger.warning(f"Data not found: {response.text}")
                raise APIError(error_msg)
            else:
                error_msg = f"APIエラー (コード: {response.status_code})"
                self.logger.error(f"API error {response.status_code}: {response.text}")
                raise APIError(error_msg)
        
        except requests.exceptions.Timeout:
            error_msg = "APIリクエストがタイムアウトしました"
            self.logger.error(f"API request timeout for URL: {url}")
            self.error_count += 1
            self.last_error = error_msg
            raise APIError(error_msg)
        
        except requests.exceptions.ConnectionError:
            error_msg = "APIサーバーに接続できません"
            self.logger.error(f"Connection error for URL: {url}")
            self.error_count += 1
            self.last_error = error_msg
            raise APIError(error_msg)
        
        except requests.exceptions.RequestException as e:
            error_msg = f"リクエストエラー: {str(e)}"
            self.logger.error(f"Request exception for URL {url}: {str(e)}")
            self.error_count += 1
            self.last_error = error_msg
            raise APIError(error_msg)
        
        except Exception as e:
            error_msg = f"予期しないエラー: {str(e)}"
            self.logger.error(f"Unexpected error for URL {url}: {str(e)}")
            self.error_count += 1
            self.last_error = error_msg
            raise APIError(error_msg)
    
    def get_current_weather(self, lat: float, lon: float, units: str = "metric") -> Optional[Dict[str, Any]]:
        """
        Get current weather data for coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            units: Temperature units ('metric', 'imperial', 'standard')
            
        Returns:
            Weather data dictionary or None if failed
        """
        url = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'units': units,
            'lang': 'ja'  # Japanese language for descriptions
        }
        
        try:
            return self._make_request(url, params)
        except (APIError, RateLimitError) as e:
            st.error(f"天気データの取得に失敗しました: {str(e)}")
            return None
    
    def get_weather_forecast(self, lat: float, lon: float, days: int = 5, units: str = "metric") -> Optional[Dict[str, Any]]:
        """
        Get weather forecast for coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of days (1-5)
            units: Temperature units
            
        Returns:
            Forecast data dictionary or None if failed
        """
        # OpenWeatherMap 5-day forecast API
        url = f"{self.base_url}/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'units': units,
            'lang': 'ja'
        }
        
        try:
            return self._make_request(url, params)
        except (APIError, RateLimitError) as e:
            st.error(f"予報データの取得に失敗しました: {str(e)}")
            return None
    
    def get_weather_alerts(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get weather alerts for coordinates (One Call API).
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Alerts data dictionary or None if failed
        """
        # Note: This requires One Call API which may need a different subscription
        url = f"{self.base_url}/onecall"
        params = {
            'lat': lat,
            'lon': lon,
            'exclude': 'minutely,hourly,daily',
            'lang': 'ja'
        }
        
        try:
            return self._make_request(url, params)
        except (APIError, RateLimitError) as e:
            self.logger.warning(f"Weather alerts not available: {str(e)}")
            return None
    
    def geocode_city(self, city_name: str, country_code: str = None, limit: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Geocode city name to coordinates.
        
        Args:
            city_name: City name to search
            country_code: Optional country code filter
            limit: Maximum number of results
            
        Returns:
            List of location dictionaries or None if failed
        """
        params = {
            'q': city_name,
            'limit': limit
        }
        
        if country_code:
            params['q'] = f"{city_name},{country_code}"
        
        try:
            url = f"{self.geocoding_url}/direct"
            return self._make_request(url, params)
        except (APIError, RateLimitError) as e:
            st.error(f"ジオコーディングに失敗しました: {str(e)}")
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float, limit: int = 1) -> Optional[List[Dict[str, Any]]]:
        """
        Reverse geocode coordinates to location names.
        
        Args:
            latitude: Latitude
            longitude: Longitude
            limit: Maximum number of results
            
        Returns:
            List of location dictionaries or None if failed
        """
        url = f"{self.geocoding_url}/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'limit': limit
        }
        
        try:
            return self._make_request(url, params)
        except (APIError, RateLimitError) as e:
            st.error(f"逆ジオコーディングに失敗しました: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test API connection and authentication.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self._check_api_key():
            return False
        
        try:
            # Test with Tokyo coordinates
            result = self.get_current_weather(35.6762, 139.6503)
            return result is not None
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get API client statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_requests': self.request_count,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1) * 100,
            'last_error': self.last_error,
            'api_key_configured': bool(self.api_key),
            'last_request_time': datetime.fromtimestamp(self.last_request_time) if self.last_request_time > 0 else None
        }
    
    def reset_statistics(self):
        """Reset request statistics."""
        self.request_count = 0
        self.error_count = 0
        self.last_error = None
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        if hasattr(self, 'session'):
            self.session.close()