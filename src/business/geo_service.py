# -*- coding: utf-8 -*-
"""
Geography service for Sky Globe application.
Handles city search, location management, and geographical calculations.
"""

import pandas as pd
import numpy as np
import streamlit as st
import random
from typing import List, Optional, Tuple, Dict, Any
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import logging

from src.data.data_models import CityInfo
from src.data.cache_manager import get_cache_manager, cached_cities_data
from src.utils.config import config


class GeoService:
    """
    Service for handling geographical operations and city management.
    Provides city search, random selection, and coordinate calculations.
    """
    
    def __init__(self):
        """Initialize geography service."""
        self.cache_manager = get_cache_manager()
        self.logger = logging.getLogger(__name__)
        self._cities_df = None
        self._countries_df = None
        
        # Initialize geocoder for fallback searches
        self.geocoder = Nominatim(
            user_agent="sky-globe-app/1.0",
            timeout=10
        )
    
    @property
    def cities_df(self) -> Optional[pd.DataFrame]:
        """Get cities dataframe with caching."""
        if self._cities_df is None:
            self._cities_df = self._load_cities_data()
        return self._cities_df
    
    @property
    def countries_df(self) -> Optional[pd.DataFrame]:
        """Get countries dataframe with caching."""
        if self._countries_df is None:
            self._countries_df = self._load_countries_data()
        return self._countries_df
    
    def _load_cities_data(self) -> Optional[pd.DataFrame]:
        """
        Load cities data from CSV file with caching.
        
        Returns:
            Cities dataframe or None if loading failed
        """
        try:
            cities_path = config.get_cities_csv_path()
            if not cities_path.exists():
                st.error(f"都市データファイルが見つかりません: {cities_path}")
                return None
            
            df = pd.read_csv(cities_path)
            
            # Data validation
            required_columns = [
                'id', 'name_en', 'name_ja', 'country_code', 'country_en', 
                'country_ja', 'latitude', 'longitude', 'timezone', 
                'continent', 'population'
            ]
            
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                st.error(f"必要な列が不足しています: {missing_columns}")
                return None
            
            # Convert data types
            df['latitude'] = pd.to_numeric(df['latitude'])
            df['longitude'] = pd.to_numeric(df['longitude'])
            df['population'] = pd.to_numeric(df['population'])
            
            # Remove invalid coordinates
            df = df[
                (df['latitude'].between(-90, 90)) & 
                (df['longitude'].between(-180, 180))
            ]
            
            self.logger.info(f"Loaded {len(df)} cities from database")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load cities data: {str(e)}")
            st.error(f"都市データの読み込みに失敗しました: {str(e)}")
            return None
    
    def _load_countries_data(self) -> Optional[pd.DataFrame]:
        """
        Load countries data from CSV file.
        
        Returns:
            Countries dataframe or None if loading failed
        """
        try:
            countries_path = config.get_countries_csv_path()
            if not countries_path.exists():
                self.logger.warning(f"Countries data file not found: {countries_path}")
                return None
            
            df = pd.read_csv(countries_path)
            self.logger.info(f"Loaded {len(df)} countries from database")
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load countries data: {str(e)}")
            return None
    
    def search_cities(self, query: str, limit: int = 10) -> List[CityInfo]:
        """
        Search cities by name (Japanese or English).
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching CityInfo objects
        """
        if not query or len(query) < config.MIN_SEARCH_LENGTH:
            return []
        
        # Check cache first
        cached_result = self.cache_manager.get('city_search', query.lower(), limit)
        if cached_result is not None:
            return cached_result
        
        if self.cities_df is None:
            return []
        
        try:
            query_lower = query.lower().strip()
            
            # Search in both Japanese and English names
            mask = (
                self.cities_df['name_ja'].str.contains(query, case=False, na=False) |
                self.cities_df['name_en'].str.lower().str.contains(query_lower, na=False) |
                self.cities_df['country_ja'].str.contains(query, case=False, na=False) |
                self.cities_df['country_en'].str.lower().str.contains(query_lower, na=False)
            )
            
            matches = self.cities_df[mask]
            
            # Sort by population (descending) and take top results
            matches = matches.sort_values('population', ascending=False).head(limit)
            
            # Convert to CityInfo objects
            results = []
            for _, row in matches.iterrows():
                try:
                    city_info = CityInfo.from_dict(row.to_dict())
                    results.append(city_info)
                except Exception as e:
                    self.logger.warning(f"Failed to create CityInfo for {row.get('name_en')}: {str(e)}")
            
            # Cache the results
            self.cache_manager.set('city_search', results, query.lower(), limit)
            
            return results
            
        except Exception as e:
            self.logger.error(f"City search failed: {str(e)}")
            return []
    
    def get_city_by_id(self, city_id: int) -> Optional[CityInfo]:
        """
        Get city information by ID.
        
        Args:
            city_id: City ID
            
        Returns:
            CityInfo object or None if not found
        """
        # Check cache first
        cached_result = self.cache_manager.get('city_by_id', city_id)
        if cached_result is not None:
            return cached_result
        
        if self.cities_df is None:
            return None
        
        try:
            match = self.cities_df[self.cities_df['id'] == city_id]
            
            if match.empty:
                return None
            
            city_data = match.iloc[0].to_dict()
            city_info = CityInfo.from_dict(city_data)
            
            # Cache the result
            self.cache_manager.set('city_by_id', city_info, city_id)
            
            return city_info
            
        except Exception as e:
            self.logger.error(f"Failed to get city by ID {city_id}: {str(e)}")
            return None
    
    def get_city_by_name(self, name: str, country_code: Optional[str] = None) -> Optional[CityInfo]:
        """
        Get city information by name.
        
        Args:
            name: City name (English or Japanese)
            country_code: Optional country code filter
            
        Returns:
            CityInfo object or None if not found
        """
        if self.cities_df is None:
            return None
        
        try:
            name_lower = name.lower().strip()
            
            # Create filter mask
            mask = (
                (self.cities_df['name_en'].str.lower() == name_lower) |
                (self.cities_df['name_ja'] == name)
            )
            
            # Add country filter if specified
            if country_code:
                mask = mask & (self.cities_df['country_code'] == country_code.upper())
            
            match = self.cities_df[mask]
            
            if match.empty:
                return None
            
            # If multiple matches, prefer the most populous city
            if len(match) > 1:
                match = match.sort_values('population', ascending=False)
            
            city_data = match.iloc[0].to_dict()
            return CityInfo.from_dict(city_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get city by name {name}: {str(e)}")
            return None
    
    def get_random_city(self, continent: Optional[str] = None) -> Optional[CityInfo]:
        """
        Get a random city, optionally filtered by continent.
        
        Args:
            continent: Optional continent filter
            
        Returns:
            Random CityInfo object or None if no cities available
        """
        if self.cities_df is None:
            return None
        
        try:
            df = self.cities_df.copy()
            
            # Apply continent filter if specified
            if continent and continent != "すべて":
                # Map Japanese continent names to English
                continent_mapping = {
                    "アジア": "Asia",
                    "ヨーロッパ": "Europe", 
                    "北アメリカ": "North America",
                    "南アメリカ": "South America",
                    "アフリカ": "Africa",
                    "オセアニア": "Oceania"
                }
                
                eng_continent = continent_mapping.get(continent, continent)
                df = df[df['continent'] == eng_continent]
            
            if df.empty:
                return None
            
            # Weight selection by population (cities with higher population more likely to be selected)
            weights = np.sqrt(df['population'])  # Square root to reduce extreme bias
            weights = weights / weights.sum()
            
            # Random selection
            selected_idx = np.random.choice(df.index, p=weights)
            city_data = df.loc[selected_idx].to_dict()
            
            return CityInfo.from_dict(city_data)
            
        except Exception as e:
            self.logger.error(f"Failed to get random city: {str(e)}")
            return None
    
    def calculate_distance(self, city1: CityInfo, city2: CityInfo) -> float:
        """
        Calculate distance between two cities in kilometers.
        
        Args:
            city1: First city
            city2: Second city
            
        Returns:
            Distance in kilometers
        """
        try:
            coord1 = (city1.latitude, city1.longitude)
            coord2 = (city2.latitude, city2.longitude)
            distance = geodesic(coord1, coord2).kilometers
            return round(distance, 2)
        except Exception as e:
            self.logger.error(f"Distance calculation failed: {str(e)}")
            return 0.0
    
    def get_nearby_cities(self, city: CityInfo, radius_km: float = 1000, limit: int = 10) -> List[Tuple[CityInfo, float]]:
        """
        Get nearby cities within specified radius.
        
        Args:
            city: Reference city
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            
        Returns:
            List of (CityInfo, distance) tuples sorted by distance
        """
        if self.cities_df is None:
            return []
        
        try:
            nearby_cities = []
            
            for _, row in self.cities_df.iterrows():
                if row['id'] == city.id:
                    continue  # Skip the reference city itself
                
                try:
                    other_city = CityInfo.from_dict(row.to_dict())
                    distance = self.calculate_distance(city, other_city)
                    
                    if distance <= radius_km:
                        nearby_cities.append((other_city, distance))
                except Exception:
                    continue
            
            # Sort by distance and return top results
            nearby_cities.sort(key=lambda x: x[1])
            return nearby_cities[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get nearby cities: {str(e)}")
            return []
    
    def get_cities_by_continent(self, continent: str) -> List[CityInfo]:
        """
        Get all cities in a specific continent.
        
        Args:
            continent: Continent name
            
        Returns:
            List of CityInfo objects
        """
        if self.cities_df is None:
            return []
        
        try:
            # Map Japanese continent names if needed
            continent_mapping = {
                "アジア": "Asia",
                "ヨーロッパ": "Europe", 
                "北アメリカ": "North America",
                "南アメリカ": "South America",
                "アフリカ": "Africa",
                "オセアニア": "Oceania"
            }
            
            eng_continent = continent_mapping.get(continent, continent)
            continent_cities = self.cities_df[self.cities_df['continent'] == eng_continent]
            
            # Sort by population descending
            continent_cities = continent_cities.sort_values('population', ascending=False)
            
            results = []
            for _, row in continent_cities.iterrows():
                try:
                    city_info = CityInfo.from_dict(row.to_dict())
                    results.append(city_info)
                except Exception:
                    continue
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to get cities by continent: {str(e)}")
            return []
    
    def get_continent_list(self) -> List[str]:
        """
        Get list of available continents in Japanese.
        
        Returns:
            List of continent names
        """
        return ["すべて", "アジア", "ヨーロッパ", "北アメリカ", "南アメリカ", "アフリカ", "オセアニア"]
    
    def geocode_address(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocode an address to coordinates using external geocoding service.
        This is a fallback for cities not in our database.
        
        Args:
            address: Address to geocode
            
        Returns:
            (latitude, longitude) tuple or None if failed
        """
        try:
            location = self.geocoder.geocode(address, timeout=10)
            if location:
                return (location.latitude, location.longitude)
            return None
        except Exception as e:
            self.logger.error(f"Geocoding failed for {address}: {str(e)}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get service statistics.
        
        Returns:
            Dictionary with statistics
        """
        if self.cities_df is None:
            return {"error": "Cities data not loaded"}
        
        return {
            "total_cities": len(self.cities_df),
            "continents": self.cities_df['continent'].value_counts().to_dict(),
            "countries": len(self.cities_df['country_code'].unique()),
            "cache_stats": self.cache_manager.get_stats()
        }