# -*- coding: utf-8 -*-
"""
Time calculation service for Sky Globe application.
Handles solar position calculations, day-night boundary, and timezone operations.
"""

import math
import numpy as np
import pytz
from datetime import datetime, timezone, timedelta
from typing import Tuple, List, Optional, Dict, Any
import logging

from src.data.data_models import DayNightBoundary
from src.data.cache_manager import get_cache_manager


class TimeService:
    """
    Service for time-related calculations including solar position and day-night boundaries.
    """
    
    def __init__(self):
        """Initialize time service."""
        self.cache_manager = get_cache_manager()
        self.logger = logging.getLogger(__name__)
        
        # Earth constants
        self.EARTH_RADIUS = 6371.0  # km
        self.EARTH_OBLIQUITY = 23.44  # degrees
        
        # Solar constants
        self.SOLAR_CONSTANT = 1367  # W/m²
        self.AU = 149597870.7  # km (Astronomical Unit)
    
    def get_current_utc_time(self) -> datetime:
        """
        Get current UTC time.
        
        Returns:
            Current UTC datetime
        """
        return datetime.now(timezone.utc)
    
    def get_local_time(self, timezone_str: str) -> Optional[datetime]:
        """
        Get current local time for a timezone.
        
        Args:
            timezone_str: Timezone string (e.g., 'Asia/Tokyo')
            
        Returns:
            Local datetime or None if timezone invalid
        """
        try:
            tz = pytz.timezone(timezone_str)
            utc_time = self.get_current_utc_time()
            local_time = utc_time.astimezone(tz)
            return local_time
        except Exception as e:
            self.logger.error(f"Invalid timezone {timezone_str}: {str(e)}")
            return None
    
    def convert_timezone(self, dt: datetime, from_tz: str, to_tz: str) -> Optional[datetime]:
        """
        Convert datetime from one timezone to another.
        
        Args:
            dt: Datetime to convert
            from_tz: Source timezone string
            to_tz: Target timezone string
            
        Returns:
            Converted datetime or None if conversion failed
        """
        try:
            from_timezone = pytz.timezone(from_tz)
            to_timezone = pytz.timezone(to_tz)
            
            # Localize the datetime if it's naive
            if dt.tzinfo is None:
                dt = from_timezone.localize(dt)
            
            # Convert to target timezone
            converted_dt = dt.astimezone(to_timezone)
            return converted_dt
        except Exception as e:
            self.logger.error(f"Timezone conversion failed: {str(e)}")
            return None
    
    def calculate_julian_day(self, dt: datetime) -> float:
        """
        Calculate Julian Day Number for astronomical calculations.
        
        Args:
            dt: Datetime object
            
        Returns:
            Julian Day Number
        """
        # Convert to UTC if not already
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        
        # Julian Day calculation
        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour
        minute = dt.minute
        second = dt.second
        
        # Algorithm for Julian Day
        if month <= 2:
            year -= 1
            month += 12
        
        a = year // 100
        b = 2 - a + (a // 4)
        
        jd = (365.25 * (year + 4716)) + (30.6001 * (month + 1)) + day + b - 1524.5
        jd += (hour + minute/60.0 + second/3600.0) / 24.0
        
        return jd
    
    def calculate_solar_declination(self, julian_day: float) -> float:
        """
        Calculate solar declination angle for given Julian day.
        
        Args:
            julian_day: Julian Day Number
            
        Returns:
            Solar declination in degrees
        """
        # Number of days since J2000.0
        n = julian_day - 2451545.0
        
        # Mean longitude of the Sun
        L = (280.460 + 0.9856474 * n) % 360
        
        # Mean anomaly of the Sun
        g = math.radians((357.528 + 0.9856003 * n) % 360)
        
        # Ecliptic longitude of the Sun
        lambda_sun = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
        
        # Solar declination
        declination = math.asin(math.sin(math.radians(self.EARTH_OBLIQUITY)) * math.sin(lambda_sun))
        
        return math.degrees(declination)
    
    def calculate_hour_angle(self, longitude: float, julian_day: float) -> float:
        """
        Calculate hour angle for given longitude and time.
        
        Args:
            longitude: Longitude in degrees
            julian_day: Julian Day Number
            
        Returns:
            Hour angle in degrees
        """
        # Greenwich hour angle
        gha = (280.460618 + 360.98564736629 * (julian_day - 2451545.0)) % 360
        
        # Local hour angle
        lha = (gha + longitude) % 360
        
        # Convert to ±180 range
        if lha > 180:
            lha -= 360
        
        return lha
    
    def calculate_sun_position(self, latitude: float, longitude: float, dt: Optional[datetime] = None) -> Dict[str, float]:
        """
        Calculate sun position (elevation and azimuth) for given coordinates and time.
        
        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            dt: Datetime (UTC), defaults to current time
            
        Returns:
            Dictionary with elevation, azimuth, and other solar parameters
        """
        if dt is None:
            dt = self.get_current_utc_time()
        
        # Cache key for this calculation
        cache_key_data = (latitude, longitude, dt.replace(second=0, microsecond=0))
        cached_result = self.cache_manager.get('sun_position', *cache_key_data)
        if cached_result is not None:
            return cached_result
        
        try:
            # Convert to radians
            lat_rad = math.radians(latitude)
            lon_rad = math.radians(longitude)
            
            # Calculate Julian Day
            jd = self.calculate_julian_day(dt)
            
            # Solar declination
            declination = math.radians(self.calculate_solar_declination(jd))
            
            # Hour angle
            hour_angle = math.radians(self.calculate_hour_angle(longitude, jd))
            
            # Solar elevation angle
            elevation_rad = math.asin(
                math.sin(lat_rad) * math.sin(declination) +
                math.cos(lat_rad) * math.cos(declination) * math.cos(hour_angle)
            )
            elevation = math.degrees(elevation_rad)
            
            # Solar azimuth angle
            azimuth_rad = math.atan2(
                math.sin(hour_angle),
                math.cos(hour_angle) * math.sin(lat_rad) - 
                math.tan(declination) * math.cos(lat_rad)
            )
            azimuth = (math.degrees(azimuth_rad) + 180) % 360
            
            # Solar zenith angle
            zenith = 90 - elevation
            
            # Air mass (simplified)
            if elevation > 0:
                air_mass = 1 / math.cos(math.radians(zenith)) if zenith < 85 else 38
            else:
                air_mass = float('inf')
            
            result = {
                'elevation': round(elevation, 2),
                'azimuth': round(azimuth, 2),
                'zenith': round(zenith, 2),
                'declination': round(math.degrees(declination), 2),
                'hour_angle': round(math.degrees(hour_angle), 2),
                'air_mass': round(air_mass, 2) if air_mass != float('inf') else None,
                'is_daylight': elevation > -6,  # Civil twilight threshold
                'julian_day': jd
            }
            
            # Cache the result for 1 minute
            self.cache_manager.set('sun_position', result, *cache_key_data)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Sun position calculation failed: {str(e)}")
            return {
                'elevation': 0,
                'azimuth': 0,
                'zenith': 90,
                'declination': 0,
                'hour_angle': 0,
                'air_mass': None,
                'is_daylight': False,
                'julian_day': 0
            }
    
    def is_daylight(self, latitude: float, longitude: float, dt: Optional[datetime] = None) -> bool:
        """
        Determine if it's daylight at given coordinates and time.
        
        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            dt: Datetime (UTC), defaults to current time
            
        Returns:
            True if daylight, False if night
        """
        sun_pos = self.calculate_sun_position(latitude, longitude, dt)
        return sun_pos['is_daylight']
    
    def calculate_day_night_boundary(self, dt: Optional[datetime] = None, num_points: int = 360) -> DayNightBoundary:
        """
        Calculate the day-night boundary (terminator line) for the entire Earth.
        
        Args:
            dt: Datetime (UTC), defaults to current time
            num_points: Number of points to calculate for the boundary
            
        Returns:
            DayNightBoundary object with coordinates
        """
        if dt is None:
            dt = self.get_current_utc_time()
        
        # Cache key for boundary calculation
        cache_time = dt.replace(minute=dt.minute//10*10, second=0, microsecond=0)  # 10-minute cache
        cached_result = self.cache_manager.get('day_night_boundary', cache_time, num_points)
        if cached_result is not None:
            return cached_result
        
        try:
            # Calculate solar declination
            jd = self.calculate_julian_day(dt)
            declination = math.radians(self.calculate_solar_declination(jd))
            
            coordinates = []
            
            # Calculate boundary points
            for i in range(num_points):
                longitude = -180 + (360 * i / num_points)
                
                # Calculate hour angle for this longitude
                hour_angle = math.radians(self.calculate_hour_angle(longitude, jd))
                
                # For the terminator line, solar elevation = 0
                # Calculate latitude where sun elevation = 0
                try:
                    # Using the solar elevation formula, solve for latitude
                    cos_lat = -math.tan(declination) / math.tan(hour_angle)
                    
                    if abs(cos_lat) <= 1:
                        latitude = math.degrees(math.acos(abs(cos_lat)))
                        if cos_lat < 0:
                            latitude = -latitude
                        
                        coordinates.append((longitude, latitude))
                    else:
                        # Handle polar day/night cases
                        if declination > 0:
                            # Summer in NH - Arctic has continuous day
                            latitude = 90 - abs(math.degrees(declination))
                        else:
                            # Winter in NH - Antarctic has continuous day
                            latitude = -90 + abs(math.degrees(declination))
                        
                        coordinates.append((longitude, latitude))
                        
                except (ZeroDivisionError, ValueError):
                    # Handle edge cases at poles
                    if abs(declination) < math.pi/4:  # Less than 45 degrees
                        latitude = 0  # Equator fallback
                    else:
                        latitude = 90 if declination > 0 else -90
                    
                    coordinates.append((longitude, latitude))
            
            # Create DayNightBoundary object
            boundary = DayNightBoundary(coordinates=coordinates, calculated_at=dt)
            
            # Cache the result
            self.cache_manager.set('day_night_boundary', boundary, cache_time, num_points)
            
            return boundary
            
        except Exception as e:
            self.logger.error(f"Day-night boundary calculation failed: {str(e)}")
            # Return empty boundary
            return DayNightBoundary(coordinates=[], calculated_at=dt)
    
    def calculate_sunrise_sunset(self, latitude: float, longitude: float, date: Optional[datetime] = None) -> Dict[str, Optional[datetime]]:
        """
        Calculate sunrise and sunset times for given coordinates and date.
        
        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            date: Date for calculation, defaults to current date
            
        Returns:
            Dictionary with sunrise and sunset times (UTC)
        """
        if date is None:
            date = self.get_current_utc_time()
        
        try:
            # Use noon for the calculation date
            noon_dt = date.replace(hour=12, minute=0, second=0, microsecond=0)
            jd = self.calculate_julian_day(noon_dt)
            
            # Solar declination for the date
            declination = math.radians(self.calculate_solar_declination(jd))
            lat_rad = math.radians(latitude)
            
            # Calculate hour angle for sunrise/sunset (sun elevation = -0.833 degrees for refraction)
            cos_hour_angle = (
                math.sin(math.radians(-0.833)) - 
                math.sin(lat_rad) * math.sin(declination)
            ) / (math.cos(lat_rad) * math.cos(declination))
            
            if abs(cos_hour_angle) > 1:
                # Polar day or night
                if cos_hour_angle < -1:
                    # Polar day (sun never sets)
                    return {'sunrise': None, 'sunset': None, 'polar_day': True, 'polar_night': False}
                else:
                    # Polar night (sun never rises)
                    return {'sunrise': None, 'sunset': None, 'polar_day': False, 'polar_night': True}
            
            # Hour angle in degrees
            hour_angle = math.degrees(math.acos(cos_hour_angle))
            
            # Solar noon in decimal hours (UTC)
            solar_noon = 12 - longitude / 15
            
            # Sunrise and sunset in decimal hours (UTC)
            sunrise_hour = solar_noon - hour_angle / 15
            sunset_hour = solar_noon + hour_angle / 15
            
            # Convert to datetime objects
            def decimal_hour_to_datetime(decimal_hour: float, base_date: datetime) -> datetime:
                hours = int(decimal_hour)
                minutes = int((decimal_hour - hours) * 60)
                seconds = int(((decimal_hour - hours) * 60 - minutes) * 60)
                
                # Handle day overflow
                if hours >= 24:
                    hours -= 24
                    base_date += timedelta(days=1)
                elif hours < 0:
                    hours += 24
                    base_date -= timedelta(days=1)
                
                return base_date.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
            
            sunrise = decimal_hour_to_datetime(sunrise_hour, date.replace(hour=0, minute=0, second=0, microsecond=0))
            sunset = decimal_hour_to_datetime(sunset_hour, date.replace(hour=0, minute=0, second=0, microsecond=0))
            
            return {
                'sunrise': sunrise,
                'sunset': sunset,
                'polar_day': False,
                'polar_night': False,
                'daylight_hours': round((sunset_hour - sunrise_hour), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Sunrise/sunset calculation failed: {str(e)}")
            return {'sunrise': None, 'sunset': None, 'polar_day': False, 'polar_night': False}
    
    def get_solar_noon(self, longitude: float, date: Optional[datetime] = None) -> datetime:
        """
        Calculate solar noon time for given longitude.
        
        Args:
            longitude: Longitude in degrees
            date: Date for calculation, defaults to current date
            
        Returns:
            Solar noon datetime (UTC)
        """
        if date is None:
            date = self.get_current_utc_time()
        
        # Solar noon occurs when the sun crosses the meridian
        solar_noon_hour = 12 - longitude / 15
        
        # Convert to datetime
        hours = int(solar_noon_hour) % 24
        minutes = int((solar_noon_hour - int(solar_noon_hour)) * 60)
        
        solar_noon = date.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        
        # Adjust for day overflow
        if solar_noon_hour >= 24:
            solar_noon += timedelta(days=1)
        elif solar_noon_hour < 0:
            solar_noon -= timedelta(days=1)
        
        return solar_noon
    
    def get_season_info(self, dt: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get seasonal information for given date.
        
        Args:
            dt: Datetime for calculation, defaults to current time
            
        Returns:
            Dictionary with season information
        """
        if dt is None:
            dt = self.get_current_utc_time()
        
        # Calculate solar declination
        jd = self.calculate_julian_day(dt)
        declination = self.calculate_solar_declination(jd)
        
        # Determine season based on declination and date
        day_of_year = dt.timetuple().tm_yday
        
        # Approximate season boundaries
        if day_of_year < 80 or day_of_year > 355:  # Dec-Feb
            season_nh = "Winter"
            season_sh = "Summer"
        elif day_of_year < 172:  # Mar-May
            season_nh = "Spring"
            season_sh = "Autumn"
        elif day_of_year < 266:  # Jun-Aug
            season_nh = "Summer"
            season_sh = "Winter"
        else:  # Sep-Nov
            season_nh = "Autumn"
            season_sh = "Spring"
        
        return {
            'northern_hemisphere': season_nh,
            'southern_hemisphere': season_sh,
            'solar_declination': round(declination, 2),
            'day_of_year': day_of_year,
            'julian_day': jd
        }