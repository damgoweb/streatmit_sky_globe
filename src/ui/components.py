# -*- coding: utf-8 -*-
"""
UI components for Sky Globe application.
Reusable components for search, weather display, settings, and interactive elements.
"""

import streamlit as st
import pandas as pd
from typing import List, Optional, Dict, Any, Callable
import logging

from src.data.data_models import CityInfo, WeatherData
from src.business.geo_service import GeoService
from src.business.weather_service import WeatherService
from src.business.globe_service import GlobeService
from src.utils.config import config


class ComponentManager:
    """
    Manager for UI components and interactive elements.
    """
    
    def __init__(self):
        """Initialize component manager."""
        self.logger = logging.getLogger(__name__)
    
    def render_search_component(self, geo_service: GeoService) -> Optional[CityInfo]:
        """
        Render city search component with autocomplete functionality.
        
        Args:
            geo_service: Geography service instance
            
        Returns:
            Selected CityInfo object or None
        """
        try:
            st.markdown("### City Search")
            
            # Search type selection
            search_type = st.radio(
                "Select search method",
                ["City Name Search", "Random Selection"],
                horizontal=True,
                key="search_type"
            )
            
            selected_city = None
            
            if search_type == "City Name Search":
                selected_city = self._render_city_search(geo_service)
            else:
                selected_city = self._render_random_selection(geo_service)
            
            return selected_city
            
        except Exception as e:
            self.logger.error(f"Failed to render search component: {str(e)}")
            st.error("Failed to load search component")
            return None
    
    def _render_city_search(self, geo_service: GeoService) -> Optional[CityInfo]:
        """
        Render city name search interface.
        
        Args:
            geo_service: Geography service instance
            
        Returns:
            Selected CityInfo object or None
        """
        try:
            # Text input for search
            search_query = st.text_input(
                "Enter city name to search",
                placeholder="Tokyo, London, Paris...",
                key="city_search_input"
            )
            
            if search_query and len(search_query) >= config.MIN_SEARCH_LENGTH:
                # Search for cities
                with st.spinner("Searching cities..."):
                    cities = geo_service.search_cities(search_query, limit=config.MAX_SEARCH_RESULTS)
                
                if cities:
                    # Display search results
                    city_options = {f"{city.display_name_ja}": city for city in cities}
                    
                    selected_name = st.selectbox(
                        f"Search results ({len(cities)} found)",
                        options=list(city_options.keys()),
                        key="city_selectbox"
                    )
                    
                    if selected_name:
                        selected_city = city_options[selected_name]
                        
                        # Show city details
                        self._render_city_preview(selected_city)
                        
                        return selected_city
                else:
                    st.warning(f"No cities found for '{search_query}'")
            
            elif search_query and len(search_query) < config.MIN_SEARCH_LENGTH:
                st.info(f"Please enter at least {config.MIN_SEARCH_LENGTH} characters to search")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to render city search: {str(e)}")
            st.error("City search failed")
            return None
    
    def _render_random_selection(self, geo_service: GeoService) -> Optional[CityInfo]:
        """
        Render random city selection interface.
        
        Args:
            geo_service: Geography service instance
            
        Returns:
            Selected CityInfo object or None
        """
        try:
            # Continent filter
            continents = geo_service.get_continent_list()
            selected_continent = st.selectbox(
                "Select continent filter",
                options=continents,
                key="continent_selectbox"
            )
            
            # Random selection button
            if st.button("Select random city", type="primary", key="random_button"):
                with st.spinner("Selecting random city..."):
                    continent_filter = None if selected_continent == "All" else selected_continent
                    random_city = geo_service.get_random_city(continent_filter)
                
                if random_city:
                    # Store in session state
                    st.session_state['selected_city'] = random_city
                    st.success(f"Random city selected: {random_city.display_name_ja}")
                    
                    # Show city details
                    self._render_city_preview(random_city)
                    
                    return random_city
                else:
                    st.error("Failed to select random city")
            
            # Show previously selected random city
            if 'selected_city' in st.session_state:
                city = st.session_state['selected_city']
                st.info(f"Current city: {city.display_name_ja}")
                return city
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to render random selection: {str(e)}")
            st.error("Random selection failed")
            return None
    
    def _render_city_preview(self, city: CityInfo) -> None:
        """
        Render a preview of selected city information.
        
        Args:
            city: CityInfo object to preview
        """
        try:
            with st.expander("City Information", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**City Name:** {city.name_ja}")
                    st.markdown(f"**Country:** {city.country_ja}")
                    st.markdown(f"**Continent:** {city.continent}")
                
                with col2:
                    st.markdown(f"**Coordinates:** {city.latitude:.4f}, {city.longitude:.4f}")
                    st.markdown(f"**Timezone:** {city.timezone}")
                    st.markdown(f"**Population:** {city.population:,}")
                    
        except Exception as e:
            self.logger.error(f"Failed to render city preview: {str(e)}")
    
    def render_weather_card(self, weather_data: WeatherData, temp_unit: str = "C") -> None:
        """
        Render weather information card.
        
        Args:
            weather_data: Weather data to display
            temp_unit: Temperature unit ('C' or 'F')
        """
        try:
            st.markdown("### Weather Information")
            
            # Format weather data for display
            weather_service = WeatherService()
            formatted_data = weather_service.format_weather_display(weather_data, temp_unit)
            
            # Main weather info
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Temperature",
                    formatted_data.get('temperature_display', 'N/A'),
                    help="Current temperature"
                )
                
            with col2:
                st.metric(
                    "Feels Like", 
                    formatted_data.get('feels_like_display', 'N/A'),
                    help="Feels like temperature"
                )
                
            with col3:
                st.markdown(
                    f"**{formatted_data.get('weather_with_emoji', weather_data.weather_description)}**"
                )
            
            # Additional details in expandable section
            with st.expander("Detailed Information", expanded=False):
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown(f"**Humidity:** {weather_data.humidity}%")
                    st.markdown(f"**Wind Speed:** {weather_data.wind_speed} m/s")
                    st.markdown(f"**Visibility:** {weather_data.visibility/1000:.1f} km")
                
                with detail_col2:
                    st.markdown(f"**Pressure:** {weather_data.pressure} hPa")
                    st.markdown(f"**Sunrise:** {weather_data.sunrise.strftime('%H:%M')}")
                    st.markdown(f"**Sunset:** {weather_data.sunset.strftime('%H:%M')}")
            
            # Update time
            st.caption(f"Last updated: {weather_data.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            self.logger.error(f"Failed to render weather card: {str(e)}")
            st.error("Failed to display weather information")
    
    def render_settings_panel(self) -> Dict[str, Any]:
        """
        Render application settings panel.
        
        Returns:
            Dictionary with current settings
        """
        try:
            st.markdown("### Settings")
            
            settings = {}
            
            # Temperature unit setting
            temp_unit = st.radio(
                "Temperature Unit",
                ["°C (Celsius)", "°F (Fahrenheit)"],
                horizontal=True,
                key="temp_unit_setting"
            )
            settings['temp_unit'] = "C" if "°C" in temp_unit else "F"
            
            # Wind speed unit setting
            wind_unit = st.selectbox(
                "Wind Speed Unit",
                ["m/s (Meters per second)", "km/h (Kilometers per hour)", "mph (Miles per hour)"],
                key="wind_unit_setting"
            )
            settings['wind_unit'] = wind_unit.split()[0]
            
            # Display options
            st.markdown("**Display Options**")
            settings['show_day_night'] = st.checkbox("Show day/night boundary", value=True, key="show_terminator")
            settings['show_city_labels'] = st.checkbox("Show city labels", value=True, key="show_labels")
            settings['auto_refresh'] = st.checkbox("Auto refresh", value=False, key="auto_refresh")
            
            if settings['auto_refresh']:
                settings['refresh_interval'] = st.slider(
                    "Refresh interval (minutes)",
                    min_value=1,
                    max_value=30,
                    value=10,
                    key="refresh_interval"
                )
            
            # Advanced settings in expandable section
            with st.expander("Advanced Settings", expanded=False):
                settings['globe_quality'] = st.selectbox(
                    "Globe display quality",
                    ["Low", "Medium", "High"],
                    index=1,
                    key="globe_quality"
                )
                
                settings['animation_speed'] = st.slider(
                    "Animation speed",
                    min_value=0.1,
                    max_value=2.0,
                    value=1.0,
                    step=0.1,
                    key="animation_speed"
                )
            
            return settings
            
        except Exception as e:
            self.logger.error(f"Failed to render settings panel: {str(e)}")
            st.error("Failed to load settings")
            return {}
    
    def render_globe_component(self, 
                             cities: List[CityInfo], 
                             weather_data: Dict[int, WeatherData],
                             selected_city: Optional[CityInfo] = None,
                             settings: Dict[str, Any] = None) -> None:
        """
        Render the 3D globe component.
        
        Args:
            cities: List of cities to display
            weather_data: Dictionary mapping city ID to weather data
            selected_city: Currently selected city
            settings: Display settings
        """
        try:
            if not settings:
                settings = {'show_day_night': True}
            
            # Create globe service and render
            globe_service = GlobeService()
            
            with st.spinner("Loading 3D globe..."):
                globe_deck = globe_service.create_complete_globe(
                    cities=cities,
                    weather_data=weather_data,
                    selected_city=selected_city,
                    show_day_night=settings.get('show_day_night', True)
                )
            
            # Display the globe
            st.pydeck_chart(globe_deck, use_container_width=True)
            
            # Globe controls
            self._render_globe_controls(globe_service, selected_city)
            
        except Exception as e:
            self.logger.error(f"Failed to render globe component: {str(e)}")
            st.error("Failed to display 3D globe")
            
            # Show fallback message
            st.info("3D globe display is not available. Please check your browser compatibility.")
            if selected_city:
                self._render_city_preview(selected_city)
    
    def _render_globe_controls(self, globe_service: GlobeService, selected_city: Optional[CityInfo]) -> None:
        """
        Render controls for the globe component.
        
        Args:
            globe_service: Globe service instance
            selected_city: Currently selected city
        """
        try:
            with st.expander("Globe Controls", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Reset view", key="reset_view"):
                        st.info("Globe view reset")
                
                with col2:
                    if st.button("Refresh globe", key="refresh_globe"):
                        st.rerun()
                
                with col3:
                    if selected_city and st.button("Focus on city", key="move_to_city"):
                        st.info(f"Focused on {selected_city.name_ja}")
                        
        except Exception as e:
            self.logger.error(f"Failed to render globe controls: {str(e)}")
    
    def render_status_panel(self, services: Dict[str, Any]) -> None:
        """
        Render application status and statistics panel.
        
        Args:
            services: Dictionary of service instances
        """
        try:
            st.markdown("### System Status")
            
            # API status
            weather_service = services.get('weather_service')
            if weather_service:
                api_connected = weather_service.test_api_connection()
                status_color = "🟢" if api_connected else "🔴"
                status_text = "Connected" if api_connected else "Disconnected"
                
                st.markdown(f"**API Status:** {status_color} {status_text}")
                
                # Get service statistics
                stats = weather_service.get_service_statistics()
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "API Calls",
                        stats['weather_service']['api_calls'],
                        help="Total API calls made today"
                    )
                
                with col2:
                    st.metric(
                        "Cache Hit Rate",
                        f"{stats['weather_service']['cache_hit_rate_percent']}%",
                        help="Percentage of requests served from cache"
                    )
                
                with col3:
                    api_remaining = stats['api_client']['requests_remaining']
                    st.metric(
                        "API Quota Remaining",
                        api_remaining,
                        help="Remaining API requests for today"
                    )
            
        except Exception as e:
            self.logger.error(f"Failed to render status panel: {str(e)}")
            st.error("Failed to display system status")
    
    def render_help_panel(self) -> None:
        """Render help and usage information panel."""
        try:
            st.markdown("### Help")
            
            with st.expander("How to Use", expanded=False):
                st.markdown("""
                **1. City Search**
                - Enter a city name to search for specific locations
                - Or use random selection to discover new cities
                
                **2. Weather Information**
                - View current weather data for selected cities
                - Detailed information includes temperature, humidity, wind, and more
                
                **3. 3D Globe Interaction**
                - Explore the interactive 3D globe showing weather patterns
                - Zoom and rotate to view different regions
                - Day/night boundary shows current solar illumination
                
                **4. Settings**
                - Change temperature units (°C/°F) and wind speed units
                - Toggle display options like day/night boundary and city labels
                """)
            
            with st.expander("Troubleshooting", expanded=False):
                st.markdown("""
                **Common Issues:**
                
                - **No weather data displayed**
                  → Check API connection status
                  → Verify internet connectivity
                
                - **3D globe not displaying**
                  → Enable WebGL in your browser
                  → Try refreshing the page
                
                - **City search not working**
                  → Check spelling of city names
                  → Try using English names for international cities
                """)
                
        except Exception as e:
            self.logger.error(f"Failed to render help panel: {str(e)}")


# Global component manager instance
component_manager = ComponentManager()


# Convenience functions for common components
def render_search_component(geo_service: GeoService) -> Optional[CityInfo]:
    """Render city search component."""
    return component_manager.render_search_component(geo_service)


def render_weather_card(weather_data: WeatherData, temp_unit: str = "C") -> None:
    """Render weather information card."""
    component_manager.render_weather_card(weather_data, temp_unit)


def render_settings_panel() -> Dict[str, Any]:
    """Render application settings panel."""
    return component_manager.render_settings_panel()


def render_globe_component(cities: List[CityInfo], 
                         weather_data: Dict[int, WeatherData],
                         selected_city: Optional[CityInfo] = None,
                         settings: Dict[str, Any] = None) -> None:
    """Render 3D globe component."""
    component_manager.render_globe_component(cities, weather_data, selected_city, settings)