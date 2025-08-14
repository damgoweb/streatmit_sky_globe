# -*- coding: utf-8 -*-
"""
Weather service for Sky Globe application.
Handles weather data retrieval, processing, and caching from OpenWeatherMap API.
"""

import streamlit as st
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any
import logging

from src.data.api_client import APIClient, APIError, RateLimitError
from src.data.data_models import WeatherData, CityInfo
from src.data.cache_manager import get_cache_manager
from src.business.time_service import TimeService


class WeatherService:
    """
    Service for weather data management and processing.
    Handles OpenWeatherMap API integration, caching, and data transformation.
    """
    
    def __init__(self):
        """Initialize weather service."""
        self.api_client = APIClient()
        self.cache_manager = get_cache_manager()
        self.time_service = TimeService()
        self.logger = logging.getLogger(__name__)
    
    def get_weather(self, city: CityInfo, units: str = "metric") -> Optional[WeatherData]:
        """
        Get current weather data for a city.
        
        Args:
            city: CityInfo object containing city details
            units: Temperature units ('metric', 'imperial', 'standard')
            
        Returns:
            WeatherData object or None if failed
        """
        # Check cache first
        cache_key = f"weather_{city.id}_{units}"
        cached_weather = self.cache_manager.get('weather', cache_key)
        if cached_weather is not None:
            return cached_weather
        
        try:
            # Call OpenWeatherMap API
            weather_data = self.api_client.get_current_weather(
                lat=city.latitude,
                lon=city.longitude,
                units=units
            )
            
            if weather_data:
                # Convert API response to WeatherData object
                weather_obj = WeatherData.from_openweather_api(weather_data)
                
                # Cache the result
                self.cache_manager.set('weather', weather_obj, cache_key)
                
                return weather_obj
            
            return None
            
        except APIError as e:
            self.logger.error(f"API error getting weather for {city.name_en}: {str(e)}")
            st.error(f"天気データの取得に失敗しました: {str(e)}")
            return None
        except RateLimitError as e:
            self.logger.warning(f"Rate limit exceeded for {city.name_en}: {str(e)}")
            st.warning("API制限に達しました。しばらく待ってから再試行してください。")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting weather for {city.name_en}: {str(e)}")
            st.error("予期しないエラーが発生しました。")
            return None
    
    def get_weather_by_coordinates(self, lat: float, lon: float, units: str = "metric") -> Optional[WeatherData]:
        """
        Get weather data by coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            units: Temperature units
            
        Returns:
            WeatherData object or None if failed
        """
        # Check cache first
        cache_key = f"weather_{lat}_{lon}_{units}"
        cached_weather = self.cache_manager.get('weather', cache_key)
        if cached_weather is not None:
            return cached_weather
        
        try:
            weather_data = self.api_client.get_current_weather(lat=lat, lon=lon, units=units)
            
            if weather_data:
                weather_obj = WeatherData.from_openweather_api(weather_data)
                self.cache_manager.set('weather', weather_obj, cache_key)
                return weather_obj
            
            return None
            
        except APIError as e:
            self.logger.error(f"API error getting weather for ({lat}, {lon}): {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting weather for ({lat}, {lon}): {str(e)}")
            return None
    
    def get_forecast(self, city: CityInfo, days: int = 5, units: str = "metric") -> Optional[List[WeatherData]]:
        """
        Get weather forecast for a city.
        
        Args:
            city: CityInfo object
            days: Number of days (1-5)
            units: Temperature units
            
        Returns:
            List of WeatherData objects or None if failed
        """
        # Validate days parameter
        if days < 1 or days > 5:
            days = 5
        
        # Check cache first
        cache_key = f"forecast_{city.id}_{days}_{units}"
        cached_forecast = self.cache_manager.get('weather', cache_key)
        if cached_forecast is not None:
            return cached_forecast
        
        try:
            forecast_data = self.api_client.get_weather_forecast(
                lat=city.latitude,
                lon=city.longitude,
                days=days,
                units=units
            )
            
            if forecast_data and 'list' in forecast_data:
                forecast_list = []
                
                for item in forecast_data['list'][:days * 8]:  # 8 forecasts per day (3-hour intervals)
                    try:
                        weather_obj = WeatherData.from_openweather_api(item)
                        forecast_list.append(weather_obj)
                    except Exception as e:
                        self.logger.warning(f"Failed to parse forecast item: {str(e)}")
                        continue
                
                # Cache the result
                if forecast_list:
                    self.cache_manager.set('weather', forecast_list, cache_key)
                
                return forecast_list
            
            return None
            
        except APIError as e:
            self.logger.error(f"API error getting forecast for {city.name_en}: {str(e)}")
            st.error(f"予報データの取得に失敗しました: {str(e)}")
            return None
        except RateLimitError as e:
            self.logger.warning(f"Rate limit exceeded for forecast {city.name_en}: {str(e)}")
            st.warning("API制限に達しました。しばらく待ってから再試行してください。")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting forecast for {city.name_en}: {str(e)}")
            return None
    
    def get_weather_alerts(self, city: CityInfo) -> Optional[List[Dict[str, Any]]]:
        """
        Get weather alerts for a city (if available).
        
        Args:
            city: CityInfo object
            
        Returns:
            List of weather alerts or None
        """
        try:
            alerts_data = self.api_client.get_weather_alerts(
                lat=city.latitude,
                lon=city.longitude
            )
            
            if alerts_data and 'alerts' in alerts_data:
                return alerts_data['alerts']
            
            return None
            
        except APIError as e:
            self.logger.error(f"API error getting alerts for {city.name_en}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting alerts for {city.name_en}: {str(e)}")
            return None
    
    def format_weather_display(self, weather: WeatherData, temp_unit: str = "C", wind_unit: str = "ms") -> Dict[str, Any]:
        """
        Format weather data for display.
        
        Args:
            weather: WeatherData object
            temp_unit: Temperature unit ('C' or 'F')
            wind_unit: Wind speed unit ('ms', 'kmh', 'mph')
            
        Returns:
            Formatted weather data dictionary
        """
        return weather.to_display_dict(temp_unit=temp_unit, wind_unit=wind_unit)
    
    def get_weather_icon_url(self, weather: WeatherData) -> str:
        """Get weather icon URL."""
        return weather.weather_icon_url
    
    def is_severe_weather(self, weather: WeatherData) -> bool:
        """
        Check if weather conditions are severe.
        
        Args:
            weather: WeatherData object
            
        Returns:
            True if weather is severe
        """
        severe_conditions = [
            'thunderstorm', 'tornado', 'squall', 'ash', 'dust',
            'sand', 'fog', 'haze', 'smoke'
        ]
        
        return (
            weather.weather_main.lower() in severe_conditions or
            weather.wind_speed > 20 or  # Strong wind > 20 m/s
            weather.temperature < -20 or  # Extreme cold < -20°C
            weather.temperature > 40  # Extreme heat > 40°C
        )
    
    def get_weather_summary(self, weather: WeatherData) -> str:
        """
        Get a brief weather summary in Japanese.
        
        Args:
            weather: WeatherData object
            
        Returns:
            Weather summary string
        """
        temp = weather.temperature
        condition = weather.weather_description
        
        # Temperature description
        if temp < 0:
            temp_desc = "非常に寒い"
        elif temp < 10:
            temp_desc = "寒い"
        elif temp < 20:
            temp_desc = "涼しい"
        elif temp < 30:
            temp_desc = "快適"
        elif temp < 35:
            temp_desc = "暖かい"
        else:
            temp_desc = "非常に暑い"
        
        return f"{condition}、{temp_desc} ({temp}°C)"
    
    def get_weather_for_city(self, city: CityInfo, units: str = "metric") -> Optional[WeatherData]:
        """
        Get weather data for a city (alias for get_weather for compatibility).
        
        Args:
            city: CityInfo object containing city details
            units: Temperature units ('metric', 'imperial', 'standard')
            
        Returns:
            WeatherData object or None if failed
        """
        return self.get_weather(city, units)
    
    def test_api_connection(self) -> bool:
        """
        Test API connection status.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Try to make a simple API call to test connectivity
            test_response = self.api_client.get_current_weather(lat=0, lon=0, units="metric")
            return test_response is not None
        except Exception as e:
            self.logger.warning(f"API connection test failed: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get weather service statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "api_stats": self.api_client.get_statistics(),
            "cache_stats": self.cache_manager.get_stats()
        }