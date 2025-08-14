# -*- coding: utf-8 -*-
"""
Styling and theme management for Sky Globe application.
Defines custom CSS, dark theme, animations, and visual components.
"""

import streamlit as st
from typing import Dict, Any
import logging


class StyleManager:
    """
    Manager for application styling and themes.
    """
    
    def __init__(self):
        """Initialize style manager."""
        self.logger = logging.getLogger(__name__)
        
        # Color palette
        self.colors = {
            # Primary colors
            'primary': '#FF6B35',
            'secondary': '#F7931E', 
            'accent': '#FFD23F',
            
            # Background colors
            'background_dark': '#0E1117',
            'background_secondary': '#262730',
            'background_light': '#FAFAFA',
            
            # Text colors
            'text_primary': '#FAFAFA',
            'text_secondary': '#CCCCCC',
            'text_muted': '#888888',
            
            # Status colors
            'success': '#00C851',
            'warning': '#FF8800',
            'error': '#FF4444',
            'info': '#33B5E5',
            
            # Weather colors
            'weather_clear': '#FFD700',
            'weather_clouds': '#C0C0C0',
            'weather_rain': '#4169E1',
            'weather_snow': '#F0F8FF',
            'weather_storm': '#8A2BE2'
        }
    
    def get_custom_css(self) -> str:
        """
        Get complete custom CSS for the application.
        
        Returns:
            CSS string
        """
        try:
            css = f"""
            <style>
            /* Import Google Fonts */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            
            /* Global Styles */
            html, body, [class*="css"] {{
                font-family: 'Inter', sans-serif;
            }}
            
            /* Hide Streamlit default elements */
            #MainMenu {{visibility: hidden;}}
            .stDeployButton {{display:none;}}
            footer {{visibility: hidden;}}
            .stApp > header {{display: none;}}
            
            /* Main container styling */
            .main .block-container {{
                padding-top: 2rem;
                padding-left: 2rem;
                padding-right: 2rem;
                max-width: none;
            }}
            
            /* Header styling */
            .main-header {{
                background: linear-gradient(135deg, {self.colors['primary']}, {self.colors['secondary']});
                padding: 2rem;
                border-radius: 15px;
                margin-bottom: 2rem;
                text-align: center;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.1);
            }}
            
            .main-header h1 {{
                color: {self.colors['text_primary']};
                font-size: 2.5rem;
                font-weight: 300;
                margin: 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }}
            
            .main-header .subtitle {{
                color: {self.colors['text_secondary']};
                font-size: 1.1rem;
                margin-top: 0.5rem;
                opacity: 0.9;
            }}
            
            /* Weather card styling */
            .weather-card {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(15px);
                border-radius: 20px;
                padding: 1.5rem;
                border: 1px solid rgba(255, 255, 255, 0.2);
                margin-bottom: 1rem;
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            
            .weather-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 12px 40px rgba(0,0,0,0.3);
            }}
            
            /* Search container styling */
            .search-container {{
                background: rgba(255, 255, 255, 0.05);
                padding: 1.5rem;
                border-radius: 15px;
                margin-bottom: 1rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }}
            
            /* Button styling */
            .stButton > button {{
                background: linear-gradient(45deg, {self.colors['primary']}, {self.colors['secondary']});
                border: none;
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 25px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 500;
                box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3);
            }}
            
            .stButton > button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(255, 107, 53, 0.4);
                background: linear-gradient(45deg, {self.colors['secondary']}, {self.colors['primary']});
            }}
            
            .stButton > button:active {{
                transform: translateY(0px);
                box-shadow: 0 2px 10px rgba(255, 107, 53, 0.3);
            }}
            
            /* Primary button specific styling */
            .stButton > button[kind="primary"] {{
                background: linear-gradient(45deg, {self.colors['accent']}, {self.colors['primary']});
                box-shadow: 0 4px 15px rgba(255, 210, 63, 0.4);
            }}
            
            .stButton > button[kind="primary"]:hover {{
                box-shadow: 0 6px 20px rgba(255, 210, 63, 0.5);
            }}
            
            /* Selectbox styling */
            .stSelectbox > div > div > select {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {self.colors['text_primary']};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                backdrop-filter: blur(5px);
            }}
            
            /* Text input styling */
            .stTextInput > div > div > input {{
                background-color: rgba(255, 255, 255, 0.1);
                color: {self.colors['text_primary']};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                backdrop-filter: blur(5px);
            }}
            
            .stTextInput > div > div > input:focus {{
                border-color: {self.colors['primary']};
                box-shadow: 0 0 10px rgba(255, 107, 53, 0.3);
            }}
            
            /* Metric styling */
            .metric-container {{
                background: rgba(255, 255, 255, 0.08);
                padding: 1rem;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                text-align: center;
                backdrop-filter: blur(5px);
            }}
            
            .stMetric {{
                background: rgba(255, 255, 255, 0.05);
                padding: 1rem;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            .stMetric > div {{
                color: {self.colors['text_primary']};
            }}
            
            /* Expander styling */
            .streamlit-expanderHeader {{
                background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            /* Radio button styling */
            .stRadio > div {{
                background: rgba(255, 255, 255, 0.05);
                padding: 1rem;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            /* Checkbox styling */
            .stCheckbox > label {{
                color: {self.colors['text_primary']};
            }}
            
            /* Slider styling */
            .stSlider > div > div > div > div {{
                background-color: {self.colors['primary']};
            }}
            
            /* Progress bar styling */
            .stProgress > div > div > div > div {{
                background-color: {self.colors['primary']};
            }}
            
            /* Success, error, info, warning styling */
            .stSuccess {{
                background-color: rgba(0, 200, 81, 0.1);
                border: 1px solid {self.colors['success']};
                border-radius: 10px;
            }}
            
            .stError {{
                background-color: rgba(255, 68, 68, 0.1);
                border: 1px solid {self.colors['error']};
                border-radius: 10px;
            }}
            
            .stInfo {{
                background-color: rgba(51, 181, 229, 0.1);
                border: 1px solid {self.colors['info']};
                border-radius: 10px;
            }}
            
            .stWarning {{
                background-color: rgba(255, 136, 0, 0.1);
                border: 1px solid {self.colors['warning']};
                border-radius: 10px;
            }}
            
            /* Sidebar styling */
            .css-1d391kg {{
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border-right: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            /* Globe container styling */
            .globe-container {{
                background: rgba(0, 0, 0, 0.3);
                border-radius: 15px;
                padding: 1rem;
                border: 1px solid rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
            }}
            
            /* Animation classes */
            .fade-in {{
                animation: fadeIn 0.5s ease-in;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            .slide-in-left {{
                animation: slideInLeft 0.5s ease-out;
            }}
            
            @keyframes slideInLeft {{
                from {{ transform: translateX(-100%); }}
                to {{ transform: translateX(0); }}
            }}
            
            .scale-in {{
                animation: scaleIn 0.3s ease-out;
            }}
            
            @keyframes scaleIn {{
                from {{ transform: scale(0.9); opacity: 0; }}
                to {{ transform: scale(1); opacity: 1; }}
            }}
            
            /* Pulse animation for loading states */
            .pulse {{
                animation: pulse 2s infinite;
            }}
            
            @keyframes pulse {{
                0% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
                100% {{ opacity: 1; }}
            }}
            
            /* Weather icon animations */
            .weather-icon {{
                width: 80px;
                height: 80px;
                margin: 0 auto;
                display: block;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
                transition: transform 0.3s ease;
            }}
            
            .weather-icon:hover {{
                transform: scale(1.1);
            }}
            
            /* Status indicators */
            .status-online {{
                color: {self.colors['success']};
                display: inline-flex;
                align-items: center;
            }}
            
            .status-online::before {{
                content: '';
                width: 8px;
                height: 8px;
                background-color: {self.colors['success']};
                border-radius: 50%;
                margin-right: 0.5rem;
                animation: pulse 2s infinite;
            }}
            
            .status-offline {{
                color: {self.colors['error']};
                display: inline-flex;
                align-items: center;
            }}
            
            .status-offline::before {{
                content: '';
                width: 8px;
                height: 8px;
                background-color: {self.colors['error']};
                border-radius: 50%;
                margin-right: 0.5rem;
            }}
            
            /* Mobile responsiveness */
            @media (max-width: 768px) {{
                .main .block-container {{
                    padding: 1rem;
                }}
                
                .main-header {{
                    padding: 1.5rem;
                    margin-bottom: 1rem;
                }}
                
                .main-header h1 {{
                    font-size: 2rem;
                }}
                
                .weather-card {{
                    padding: 1rem;
                }}
            }}
            
            /* Custom scrollbar */
            ::-webkit-scrollbar {{
                width: 8px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: rgba(255, 107, 53, 0.6);
                border-radius: 4px;
            }}
            
            ::-webkit-scrollbar-thumb:hover {{
                background: rgba(255, 107, 53, 0.8);
            }}
            
            /* Tooltip styling */
            .tooltip {{
                position: relative;
                display: inline-block;
            }}
            
            .tooltip .tooltiptext {{
                visibility: hidden;
                width: 200px;
                background-color: rgba(0, 0, 0, 0.8);
                color: {self.colors['text_primary']};
                text-align: center;
                border-radius: 8px;
                padding: 8px;
                position: absolute;
                z-index: 1;
                bottom: 125%;
                left: 50%;
                margin-left: -100px;
                opacity: 0;
                transition: opacity 0.3s;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            
            .tooltip:hover .tooltiptext {{
                visibility: visible;
                opacity: 1;
            }}
            </style>
            """
            
            return css
            
        except Exception as e:
            self.logger.error(f"Failed to generate custom CSS: {str(e)}")
            return "<style></style>"
    
    def get_main_header_html(self) -> str:
        """
        Get HTML for the main application header.
        
        Returns:
            HTML string for header
        """
        try:
            return f"""
            <div class="main-header fade-in">
                <h1>🌍 Sky Globe</h1>
                <p class="subtitle">Global Weather Visualization</p>
            </div>
            """
        except Exception as e:
            self.logger.error(f"Failed to generate header HTML: {str(e)}")
            return "<div><h1>🌍 Sky Globe - Global Weather</h1></div>"
    
    def get_weather_card_html(self, weather_data: Dict[str, Any], city_name: str) -> str:
        """
        Get HTML for weather information card.
        
        Args:
            weather_data: Weather data dictionary
            city_name: Name of the city
            
        Returns:
            HTML string for weather card
        """
        try:
            return f"""
            <div class="weather-card scale-in">
                <h3 style="margin-top: 0; color: {self.colors['text_primary']};">
                    🏙️ {city_name} Weather
                </h3>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 2.5rem; font-weight: 300; color: {self.colors['accent']};">
                            {weather_data.get('temperature', 'N/A')}°C
                        </span>
                        <p style="color: {self.colors['text_secondary']}; margin: 0;">
                            Feels like {weather_data.get('feels_like', 'N/A')}°C
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <img class="weather-icon" src="{weather_data.get('icon_url', '')}" alt="Weather icon">
                        <p style="color: {self.colors['text_primary']}; margin: 0.5rem 0 0 0;">
                            {weather_data.get('weather', 'N/A')}
                        </p>
                    </div>
                </div>
            </div>
            """
        except Exception as e:
            self.logger.error(f"Failed to generate weather card HTML: {str(e)}")
            return "<div class='weather-card'>Weather information unavailable</div>"
    
    def get_status_indicator_html(self, status: bool, label: str) -> str:
        """
        Get HTML for status indicator.
        
        Args:
            status: True for online/success, False for offline/error
            label: Status label
            
        Returns:
            HTML string for status indicator
        """
        try:
            css_class = "status-online" if status else "status-offline"
            return f'<span class="{css_class}">{label}</span>'
        except Exception as e:
            self.logger.error(f"Failed to generate status indicator HTML: {str(e)}")
            return f"<span>{label}</span>"
    
    def apply_custom_styles(self) -> None:
        """Apply custom styles to the Streamlit application."""
        try:
            st.markdown(self.get_custom_css(), unsafe_allow_html=True)
        except Exception as e:
            self.logger.error(f"Failed to apply custom styles: {str(e)}")
    
    def get_theme_colors(self) -> Dict[str, str]:
        """
        Get current theme color palette.
        
        Returns:
            Dictionary with color values
        """
        return self.colors.copy()
    
    def set_theme_color(self, color_name: str, color_value: str) -> None:
        """
        Set a theme color.
        
        Args:
            color_name: Name of the color
            color_value: Hex color value
        """
        try:
            self.colors[color_name] = color_value
            self.logger.info(f"Theme color '{color_name}' set to '{color_value}'")
        except Exception as e:
            self.logger.error(f"Failed to set theme color: {str(e)}")


# Global style manager instance
style_manager = StyleManager()


# Convenience functions
def apply_custom_styles() -> None:
    """Apply custom styles to the application."""
    style_manager.apply_custom_styles()


def get_main_header_html() -> str:
    """Get HTML for main header."""
    return style_manager.get_main_header_html()


def get_weather_card_html(weather_data: Dict[str, Any], city_name: str) -> str:
    """Get HTML for weather card."""
    return style_manager.get_weather_card_html(weather_data, city_name)


def get_status_indicator_html(status: bool, label: str) -> str:
    """Get HTML for status indicator."""
    return style_manager.get_status_indicator_html(status, label)


def get_theme_colors() -> Dict[str, str]:
    """Get current theme colors."""
    return style_manager.get_theme_colors()