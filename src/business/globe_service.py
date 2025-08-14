# -*- coding: utf-8 -*-
"""
Globe service for Sky Globe application.
Handles 3D globe rendering, layer management, and interactive features using Pydeck.
"""

import pydeck as pdk
import pandas as pd
import numpy as np
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
import logging

from src.data.data_models import CityInfo, WeatherData, DayNightBoundary
from src.business.time_service import TimeService
from src.utils.config import config


class GlobeService:
    """
    Service for 3D globe rendering and visualization management.
    Creates and manages Pydeck layers for cities, weather, and day-night boundaries.
    """
    
    def __init__(self):
        """Initialize globe service."""
        self.time_service = TimeService()
        self.logger = logging.getLogger(__name__)
        
        # Globe configuration
        self.EARTH_RADIUS = 6371000  # meters
        self.DEFAULT_VIEW_STATE = pdk.ViewState(
            longitude=139.6917,  # Tokyo
            latitude=35.6895,
            zoom=1.5,
            pitch=0,
            bearing=0
        )
        
        # Layer colors and styling
        self.COLORS = {
            'day': [255, 255, 200, 80],      # Light yellow for day areas
            'night': [50, 50, 100, 120],     # Dark blue for night areas
            'terminator': [255, 255, 0, 150], # Yellow for day-night boundary
            'city_default': [255, 255, 255, 200],  # White for cities
            'city_selected': [255, 100, 100, 255], # Red for selected city
            'weather_clear': [255, 255, 0, 180],   # Yellow for clear
            'weather_clouds': [200, 200, 200, 180], # Gray for clouds
            'weather_rain': [100, 150, 255, 180],   # Blue for rain
            'weather_snow': [255, 255, 255, 180],   # White for snow
            'weather_storm': [150, 100, 200, 180]   # Purple for storms
        }
    
    def create_basic_globe(self, center_city: Optional[CityInfo] = None) -> pdk.Deck:
        """
        Create a basic 3D globe with Earth texture.
        
        Args:
            center_city: Optional city to center the view on
            
        Returns:
            Pydeck Deck object
        """
        try:
            # Set view state
            if center_city:
                view_state = pdk.ViewState(
                    longitude=center_city.longitude,
                    latitude=center_city.latitude,
                    zoom=2.5,
                    pitch=0,
                    bearing=0
                )
            else:
                view_state = self.DEFAULT_VIEW_STATE
            
            # Create basic globe layer (background)
            globe_layer = pdk.Layer(
                "SolidPolygonLayer",
                data=[],
                get_polygon=[],
                get_fill_color=[50, 100, 150, 255],  # Ocean blue
                pickable=False
            )
            
            # Create deck
            deck = pdk.Deck(
                layers=[globe_layer],
                initial_view_state=view_state,
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                tooltip={
                    'html': '<b>{name}</b><br/>Temperature: {temperature}°C<br/>Weather: {weather}',
                    'style': {
                        'backgroundColor': 'rgba(0,0,0,0.8)',
                        'color': 'white',
                        'fontSize': '12px',
                        'padding': '10px'
                    }
                }
            )
            
            return deck
            
        except Exception as e:
            self.logger.error(f"Failed to create basic globe: {str(e)}")
            # Return minimal deck on error
            return pdk.Deck(layers=[], initial_view_state=self.DEFAULT_VIEW_STATE)
    
    def create_cities_layer(self, cities: List[CityInfo], selected_city: Optional[CityInfo] = None) -> pdk.Layer:
        """
        Create a layer showing cities as points on the globe.
        
        Args:
            cities: List of cities to display
            selected_city: Currently selected city (highlighted)
            
        Returns:
            Pydeck Layer object
        """
        try:
            if not cities:
                return None
            
            # Prepare data
            data = []
            for city in cities:
                color = self.COLORS['city_selected'] if (selected_city and city.id == selected_city.id) else self.COLORS['city_default']
                radius = 50000 if (selected_city and city.id == selected_city.id) else 30000  # meters
                
                data.append({
                    'id': city.id,
                    'city_name': city.name_ja,
                    'name': city.name_ja,
                    'name_en': city.name_en,
                    'country': city.country_ja,
                    'latitude': city.latitude,
                    'longitude': city.longitude,
                    'population': city.population,
                    'temperature': 'N/A',  # Default for cities without weather data
                    'weather': 'No data',
                    'color': color,
                    'radius': radius,
                    'elevation': 10000 if (selected_city and city.id == selected_city.id) else 0
                })
            
            # Create ScatterplotLayer
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=data,
                get_position=["longitude", "latitude"],
                get_color="color",
                get_radius="radius",
                get_elevation="elevation",
                radius_scale=1,
                radius_min_pixels=3,
                radius_max_pixels=20,
                pickable=True,
                auto_highlight=True,
                highlight_color=[255, 255, 0, 200]
            )
            
            return layer
            
        except Exception as e:
            self.logger.error(f"Failed to create cities layer: {str(e)}")
            return None
    
    def create_weather_layer(self, weather_data_list: List[Tuple[CityInfo, WeatherData]]) -> pdk.Layer:
        """
        Create a layer showing weather information for cities.
        
        Args:
            weather_data_list: List of (CityInfo, WeatherData) tuples
            
        Returns:
            Pydeck Layer object
        """
        try:
            if not weather_data_list:
                return None
            
            # Prepare data
            data = []
            for city, weather in weather_data_list:
                if weather is None:
                    continue
                
                # Determine color based on weather condition
                color = self._get_weather_color(weather.weather_main)
                
                # Size based on temperature (warmer = larger, normalized)
                temp_normalized = max(0.2, min(2.0, (weather.temperature + 20) / 50))
                radius = 40000 * temp_normalized
                
                # Elevation based on weather intensity
                elevation = self._get_weather_elevation(weather)
                
                data.append({
                    'city_id': city.id,
                    'city_name': city.name_ja,
                    'country': city.country_ja,
                    'latitude': city.latitude,
                    'longitude': city.longitude,
                    'temperature': weather.temperature,
                    'weather': weather.weather_description,
                    'weather_main': weather.weather_main,
                    'icon': weather.weather_icon,
                    'color': color,
                    'radius': radius,
                    'elevation': elevation
                })
            
            # Create ColumnLayer for 3D weather visualization
            layer = pdk.Layer(
                "ColumnLayer",
                data=data,
                get_position=["longitude", "latitude"],
                get_color="color",
                get_radius="radius",
                get_elevation="elevation",
                radius_scale=1,
                elevation_scale=1,
                pickable=True,
                auto_highlight=True
            )
            
            return layer
            
        except Exception as e:
            self.logger.error(f"Failed to create weather layer: {str(e)}")
            return None
    
    def create_day_night_layer(self, boundary: DayNightBoundary) -> pdk.Layer:
        """
        Create a layer showing the day-night boundary (terminator line).
        
        Args:
            boundary: DayNightBoundary object with coordinates
            
        Returns:
            Pydeck Layer object
        """
        try:
            if not boundary.coordinates:
                return None
            
            # Prepare path data for line
            path_data = [{
                'path': [[lon, lat] for lon, lat in boundary.coordinates],
                'color': self.COLORS['terminator'],
                'width': 3
            }]
            
            # Create PathLayer
            layer = pdk.Layer(
                "PathLayer",
                data=path_data,
                get_path="path",
                get_color="color",
                get_width="width",
                width_scale=20,
                width_min_pixels=2,
                pickable=False
            )
            
            return layer
            
        except Exception as e:
            self.logger.error(f"Failed to create day-night layer: {str(e)}")
            return None
    
    def create_day_night_regions_layer(self) -> pdk.Layer:
        """
        Create a layer showing day and night regions (experimental).
        This creates hemisphere polygons to approximate day/night areas.
        
        Returns:
            Pydeck Layer object
        """
        try:
            # Get current solar declination to determine day/night split
            sun_info = self.time_service.get_season_info()
            declination = sun_info['solar_declination']
            
            # Create simplified day/night regions
            # This is a simplified representation - actual implementation would be more complex
            regions = []
            
            # Day region (rough approximation)
            day_coords = []
            night_coords = []
            
            for lon in range(-180, 180, 10):
                # Simple calculation - actual terminator is more complex
                lat_boundary = declination * np.cos(np.radians(lon * 15))  # Rough approximation
                
                # Day region points
                day_coords.extend([
                    [lon, min(90, lat_boundary + 90)],
                    [lon + 10, min(90, lat_boundary + 90)]
                ])
                
                # Night region points
                night_coords.extend([
                    [lon, max(-90, lat_boundary - 90)],
                    [lon + 10, max(-90, lat_boundary - 90)]
                ])
            
            # Add day and night regions
            if day_coords:
                regions.append({
                    'polygon': day_coords,
                    'color': self.COLORS['day'],
                    'type': 'day'
                })
            
            if night_coords:
                regions.append({
                    'polygon': night_coords,
                    'color': self.COLORS['night'],
                    'type': 'night'
                })
            
            # Create PolygonLayer
            layer = pdk.Layer(
                "PolygonLayer",
                data=regions,
                get_polygon="polygon",
                get_fill_color="color",
                get_line_color=[0, 0, 0, 0],
                pickable=False,
                auto_highlight=False
            )
            
            return layer
            
        except Exception as e:
            self.logger.error(f"Failed to create day-night regions layer: {str(e)}")
            return None
    
    def _get_weather_color(self, weather_main: str) -> List[int]:
        """
        Get color for weather condition.
        
        Args:
            weather_main: Main weather condition
            
        Returns:
            RGBA color list
        """
        weather_colors = {
            'Clear': self.COLORS['weather_clear'],
            'Clouds': self.COLORS['weather_clouds'],
            'Rain': self.COLORS['weather_rain'],
            'Drizzle': self.COLORS['weather_rain'],
            'Snow': self.COLORS['weather_snow'],
            'Thunderstorm': self.COLORS['weather_storm'],
            'Mist': self.COLORS['weather_clouds'],
            'Fog': self.COLORS['weather_clouds'],
            'Haze': self.COLORS['weather_clouds']
        }
        
        return weather_colors.get(weather_main, self.COLORS['city_default'])
    
    def _get_weather_elevation(self, weather: WeatherData) -> float:
        """
        Calculate elevation for weather visualization based on conditions.
        
        Args:
            weather: WeatherData object
            
        Returns:
            Elevation in meters
        """
        # Base elevation
        base_elevation = 50000  # 50km
        
        # Adjust based on weather conditions
        if weather.weather_main in ['Thunderstorm']:
            return base_elevation * 2  # High for storms
        elif weather.weather_main in ['Rain', 'Drizzle']:
            return base_elevation * 1.5  # Medium for rain
        elif weather.weather_main in ['Snow']:
            return base_elevation * 1.3  # Medium-high for snow
        elif weather.weather_main in ['Clouds']:
            return base_elevation * 1.1  # Slightly higher for clouds
        else:
            return base_elevation  # Base for clear weather
    
    def create_complete_globe(self, 
                            cities: List[CityInfo], 
                            weather_data: Dict[int, WeatherData],
                            selected_city: Optional[CityInfo] = None,
                            show_day_night: bool = True) -> pdk.Deck:
        """
        Create a complete globe with all layers.
        
        Args:
            cities: List of cities to display
            weather_data: Dictionary mapping city ID to weather data
            selected_city: Currently selected city
            show_day_night: Whether to show day-night boundary
            
        Returns:
            Complete Pydeck Deck object
        """
        try:
            layers = []
            
            # Add cities layer
            cities_layer = self.create_cities_layer(cities, selected_city)
            if cities_layer:
                layers.append(cities_layer)
            
            # Add weather layer
            weather_list = []
            for city in cities:
                weather = weather_data.get(city.id)
                if weather:
                    weather_list.append((city, weather))
            
            weather_layer = self.create_weather_layer(weather_list)
            if weather_layer:
                layers.append(weather_layer)
            
            # Add day-night boundary if requested
            if show_day_night:
                try:
                    boundary = self.time_service.calculate_day_night_boundary()
                    day_night_layer = self.create_day_night_layer(boundary)
                    if day_night_layer:
                        layers.append(day_night_layer)
                except Exception as e:
                    self.logger.warning(f"Failed to add day-night layer: {str(e)}")
            
            # Set view state
            if selected_city:
                view_state = pdk.ViewState(
                    longitude=selected_city.longitude,
                    latitude=selected_city.latitude,
                    zoom=3,
                    pitch=30,
                    bearing=0
                )
            else:
                view_state = self.DEFAULT_VIEW_STATE
            
            # Create complete deck
            deck = pdk.Deck(
                layers=layers,
                initial_view_state=view_state,
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                tooltip={
                    'html': '''
                    <div style="background-color: rgba(0,0,0,0.8); color: white; padding: 10px; border-radius: 5px;">
                        <b>{city_name}</b><br/>
                        🌡️ {temperature}°C<br/>
                        🌤️ {weather}<br/>
                        🏙️ {country}
                    </div>
                    ''',
                    'style': {
                        'fontSize': '12px'
                    }
                }
            )
            
            return deck
            
        except Exception as e:
            self.logger.error(f"Failed to create complete globe: {str(e)}")
            return self.create_basic_globe()
    
    def update_view_state(self, deck: pdk.Deck, longitude: float, latitude: float, zoom: float = 3) -> pdk.Deck:
        """
        Update the view state of an existing deck.
        
        Args:
            deck: Existing Pydeck Deck
            longitude: New longitude
            latitude: New latitude
            zoom: New zoom level
            
        Returns:
            Updated Pydeck Deck
        """
        try:
            new_view_state = pdk.ViewState(
                longitude=longitude,
                latitude=latitude,
                zoom=zoom,
                pitch=deck.initial_view_state.pitch if deck.initial_view_state else 30,
                bearing=deck.initial_view_state.bearing if deck.initial_view_state else 0
            )
            
            deck.initial_view_state = new_view_state
            return deck
            
        except Exception as e:
            self.logger.error(f"Failed to update view state: {str(e)}")
            return deck
    
    def get_optimal_zoom(self, cities: List[CityInfo]) -> float:
        """
        Calculate optimal zoom level to show all cities.
        
        Args:
            cities: List of cities to include in view
            
        Returns:
            Optimal zoom level
        """
        if not cities:
            return 1.5
        
        try:
            lats = [city.latitude for city in cities]
            lons = [city.longitude for city in cities]
            
            lat_range = max(lats) - min(lats)
            lon_range = max(lons) - min(lons)
            
            # Simple zoom calculation based on coordinate range
            max_range = max(lat_range, lon_range)
            
            if max_range > 100:
                return 1
            elif max_range > 50:
                return 2
            elif max_range > 20:
                return 3
            elif max_range > 10:
                return 4
            else:
                return 5
                
        except Exception as e:
            self.logger.error(f"Failed to calculate optimal zoom: {str(e)}")
            return 2.5