# -*- coding: utf-8 -*-
"""
Data models for Sky Globe application.
Defines dataclasses for city information and weather data.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
import json


@dataclass
class CityInfo:
    """Data model for city information."""
    
    id: int
    name_en: str
    name_ja: str
    country_code: str
    country_en: str
    country_ja: str
    latitude: float
    longitude: float
    timezone: str
    continent: str
    population: int
    
    def __post_init__(self):
        """Validate data after initialization."""
        # Validate coordinates
        if not (-90 <= self.latitude <= 90):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not (-180 <= self.longitude <= 180):
            raise ValueError(f"Invalid longitude: {self.longitude}")
        
        # Validate required fields
        if not self.name_en or not self.name_ja:
            raise ValueError("City name (English and Japanese) is required")
        if not self.country_code or len(self.country_code) != 2:
            raise ValueError("Valid 2-letter country code is required")
    
    @property
    def coordinates(self) -> Tuple[float, float]:
        """Get coordinates as (longitude, latitude) tuple for mapping."""
        return (self.longitude, self.latitude)
    
    @property
    def display_name_ja(self) -> str:
        """Get display name in Japanese."""
        return f"{self.name_ja} ({self.country_ja})"
    
    @property
    def display_name_en(self) -> str:
        """Get display name in English."""
        return f"{self.name_en} ({self.country_en})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format suitable for Pydeck."""
        return {
            'id': self.id,
            'name': self.name_ja,
            'name_en': self.name_en,
            'coordinates': [self.longitude, self.latitude],
            'lat': self.latitude,
            'lon': self.longitude,
            'country': self.country_ja,
            'country_en': self.country_en,
            'continent': self.continent,
            'population': self.population,
            'timezone': self.timezone
        }
    
    def to_geojson_feature(self) -> Dict[str, Any]:
        """Convert to GeoJSON feature format."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "id": self.id,
                "name": self.name_ja,
                "name_en": self.name_en,
                "country": self.country_ja,
                "country_en": self.country_en,
                "country_code": self.country_code,
                "continent": self.continent,
                "population": self.population,
                "timezone": self.timezone
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CityInfo':
        """Create CityInfo instance from dictionary."""
        return cls(
            id=data['id'],
            name_en=data['name_en'],
            name_ja=data['name_ja'],
            country_code=data['country_code'],
            country_en=data['country_en'],
            country_ja=data['country_ja'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            timezone=data['timezone'],
            continent=data['continent'],
            population=int(data['population'])
        )


@dataclass
class WeatherData:
    """Data model for weather information."""
    
    city_id: int
    city_name: str
    country_code: str
    coordinates: Tuple[float, float]
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    wind_speed: float
    wind_direction: int
    visibility: int
    weather_main: str
    weather_description: str
    weather_icon: str
    timezone_offset: int
    local_time: datetime
    sunrise: datetime
    sunset: datetime
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate weather data after initialization."""
        # Validate temperature ranges (extreme but possible values)
        if not (-100 <= self.temperature <= 70):
            raise ValueError(f"Invalid temperature: {self.temperature}°C")
        
        # Validate humidity (0-100%)
        if not (0 <= self.humidity <= 100):
            raise ValueError(f"Invalid humidity: {self.humidity}%")
        
        # Validate wind speed (0-200+ m/s for extreme cases)
        if self.wind_speed < 0:
            raise ValueError(f"Invalid wind speed: {self.wind_speed}")
        
        # Validate wind direction (0-360 degrees)
        if not (0 <= self.wind_direction <= 360):
            raise ValueError(f"Invalid wind direction: {self.wind_direction}°")
    
    @property
    def temperature_fahrenheit(self) -> float:
        """Get temperature in Fahrenheit."""
        return round(self.temperature * 9/5 + 32, 1)
    
    @property
    def feels_like_fahrenheit(self) -> float:
        """Get feels-like temperature in Fahrenheit."""
        return round(self.feels_like * 9/5 + 32, 1)
    
    @property
    def wind_speed_mph(self) -> float:
        """Get wind speed in mph."""
        return round(self.wind_speed * 2.237, 1)
    
    @property
    def wind_speed_kmh(self) -> float:
        """Get wind speed in km/h."""
        return round(self.wind_speed * 3.6, 1)
    
    @property
    def is_day(self) -> bool:
        """Check if current time is during daylight hours."""
        return self.sunrise <= self.local_time <= self.sunset
    
    @property
    def weather_icon_url(self) -> str:
        """Get OpenWeatherMap icon URL."""
        return f"https://openweathermap.org/img/wn/{self.weather_icon}@2x.png"
    
    def to_display_dict(self, temp_unit: str = "C", wind_unit: str = "ms") -> Dict[str, Any]:
        """
        Convert to display dictionary with specified units.
        
        Args:
            temp_unit: Temperature unit ('C' for Celsius, 'F' for Fahrenheit)
            wind_unit: Wind speed unit ('ms', 'kmh', 'mph')
        """
        # Temperature conversion
        temp = self.temperature
        feels = self.feels_like
        temp_symbol = "°C"
        
        if temp_unit.upper() == "F":
            temp = self.temperature_fahrenheit
            feels = self.feels_like_fahrenheit
            temp_symbol = "°F"
        
        # Wind speed conversion
        wind = self.wind_speed
        wind_symbol = "m/s"
        
        if wind_unit.lower() == "kmh":
            wind = self.wind_speed_kmh
            wind_symbol = "km/h"
        elif wind_unit.lower() == "mph":
            wind = self.wind_speed_mph
            wind_symbol = "mph"
        
        return {
            'city': self.city_name,
            'temperature': temp,
            'temperature_unit': temp_symbol,
            'feels_like': feels,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'wind_speed': wind,
            'wind_unit': wind_symbol,
            'wind_direction': self.wind_direction,
            'visibility': self.visibility,
            'weather': self.weather_description,
            'weather_main': self.weather_main,
            'icon': self.weather_icon,
            'icon_url': self.weather_icon_url,
            'is_day': self.is_day,
            'local_time': self.local_time.strftime('%Y-%m-%d %H:%M:%S'),
            'sunrise': self.sunrise.strftime('%H:%M'),
            'sunset': self.sunset.strftime('%H:%M'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'city_id': self.city_id,
            'city_name': self.city_name,
            'country_code': self.country_code,
            'coordinates': self.coordinates,
            'temperature': self.temperature,
            'feels_like': self.feels_like,
            'humidity': self.humidity,
            'pressure': self.pressure,
            'wind_speed': self.wind_speed,
            'wind_direction': self.wind_direction,
            'visibility': self.visibility,
            'weather_main': self.weather_main,
            'weather_description': self.weather_description,
            'weather_icon': self.weather_icon,
            'timezone_offset': self.timezone_offset,
            'local_time': self.local_time.isoformat(),
            'sunrise': self.sunrise.isoformat(),
            'sunset': self.sunset.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_openweather_api(cls, api_data: Dict[str, Any]) -> 'WeatherData':
        """
        Create WeatherData instance from OpenWeatherMap API response.
        
        Args:
            api_data: Raw API response from OpenWeatherMap
            
        Returns:
            WeatherData instance
        """
        coord = api_data['coord']
        main = api_data['main']
        weather = api_data['weather'][0]
        wind = api_data.get('wind', {})
        sys = api_data['sys']
        
        # Calculate local time
        timezone_offset = api_data.get('timezone', 0)
        local_time = datetime.utcnow().replace(microsecond=0)
        local_time = local_time + timedelta(seconds=timezone_offset)
        
        # Convert sunrise/sunset timestamps with timezone offset
        sunrise = datetime.utcfromtimestamp(sys['sunrise']) + timedelta(seconds=timezone_offset)
        sunset = datetime.utcfromtimestamp(sys['sunset']) + timedelta(seconds=timezone_offset)
        
        return cls(
            city_id=api_data.get('id', 0),
            city_name=api_data['name'],
            country_code=sys['country'],
            coordinates=(coord['lon'], coord['lat']),
            temperature=main['temp'],
            feels_like=main['feels_like'],
            humidity=main['humidity'],
            pressure=main['pressure'],
            wind_speed=wind.get('speed', 0.0),
            wind_direction=wind.get('deg', 0),
            visibility=api_data.get('visibility', 10000),
            weather_main=weather['main'],
            weather_description=weather['description'],
            weather_icon=weather['icon'],
            timezone_offset=timezone_offset,
            local_time=local_time,
            sunrise=sunrise,
            sunset=sunset
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeatherData':
        """Create WeatherData instance from dictionary."""
        return cls(
            city_id=data['city_id'],
            city_name=data['city_name'],
            country_code=data['country_code'],
            coordinates=tuple(data['coordinates']),
            temperature=data['temperature'],
            feels_like=data['feels_like'],
            humidity=data['humidity'],
            pressure=data['pressure'],
            wind_speed=data['wind_speed'],
            wind_direction=data['wind_direction'],
            visibility=data['visibility'],
            weather_main=data['weather_main'],
            weather_description=data['weather_description'],
            weather_icon=data['weather_icon'],
            timezone_offset=data['timezone_offset'],
            local_time=datetime.fromisoformat(data['local_time']),
            sunrise=datetime.fromisoformat(data['sunrise']),
            sunset=datetime.fromisoformat(data['sunset']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )


@dataclass
class DayNightBoundary:
    """Data model for day-night boundary line."""
    
    coordinates: list[Tuple[float, float]]
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_geojson(self) -> Dict[str, Any]:
        """Convert to GeoJSON format for mapping."""
        return {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[lon, lat] for lon, lat in self.coordinates]
            },
            "properties": {
                "type": "day_night_boundary",
                "calculated_at": self.calculated_at.isoformat()
            }
        }
    
    def to_pydeck_data(self) -> list[Dict[str, Any]]:
        """Convert to format suitable for Pydeck LineLayer."""
        return [{
            "path": [[lon, lat] for lon, lat in self.coordinates],
            "color": [255, 255, 0, 100],  # Semi-transparent yellow
            "width": 2
        }]