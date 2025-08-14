# -*- coding: utf-8 -*-
"""
Layout management for Sky Globe application.
Defines page layouts, column structures, and responsive design elements.
"""

import streamlit as st
from typing import Optional, Dict, Any, Callable
import logging

from src.ui.styles import apply_custom_styles, get_main_header_html
from src.utils.config import config


class LayoutManager:
    """
    Manager for application layouts and responsive design.
    """
    
    def __init__(self):
        """Initialize layout manager."""
        self.logger = logging.getLogger(__name__)
    
    def setup_page_config(self, title: str = "Sky Globe - Global Weather") -> None:
        """
        Setup Streamlit page configuration.
        
        Args:
            title: Page title
        """
        try:
            st.set_page_config(
                page_title=title,
                page_icon="🌍",
                layout="wide",
                initial_sidebar_state="expanded",
                menu_items={
                    'Get Help': 'https://github.com/your-repo/sky-globe',
                    'Report a bug': 'https://github.com/your-repo/sky-globe/issues',
                    'About': "# Sky Globe\nGlobal weather visualization web application"
                }
            )
            
            # Apply custom styles
            apply_custom_styles()
            
        except Exception as e:
            self.logger.error(f"Failed to setup page config: {str(e)}")
    
    def render_header(self, show_stats: bool = False) -> None:
        """
        Render the main application header.
        
        Args:
            show_stats: Whether to show application statistics
        """
        try:
            # Main header
            st.markdown(get_main_header_html(), unsafe_allow_html=True)
            
            # Optional stats display
            if show_stats and config.is_debug():
                self._render_debug_stats()
                
        except Exception as e:
            self.logger.error(f"Failed to render header: {str(e)}")
            st.title("🌍 Sky Globe - Global Weather")
    
    def render_main_layout(self, 
                          sidebar_content: Callable = None,
                          main_content: Callable = None,
                          sidebar_width: float = 0.3) -> None:
        """
        Render the main application layout with sidebar and main content.
        
        Args:
            sidebar_content: Function to render sidebar content
            main_content: Function to render main content
            sidebar_width: Width ratio for sidebar (0.0 to 1.0)
        """
        try:
            # Create responsive columns
            col_ratios = [sidebar_width, 1 - sidebar_width]
            col1, col2 = st.columns(col_ratios)
            
            # Render sidebar content
            with col1:
                if sidebar_content:
                    sidebar_content()
                else:
                    self._render_default_sidebar()
            
            # Render main content
            with col2:
                if main_content:
                    main_content()
                else:
                    self._render_default_main()
                    
        except Exception as e:
            self.logger.error(f"Failed to render main layout: {str(e)}")
            # Fallback to simple layout
            if main_content:
                main_content()
    
    def render_two_column_layout(self,
                                left_content: Callable = None,
                                right_content: Callable = None,
                                column_ratio: tuple = (1, 1)) -> None:
        """
        Render a two-column layout.
        
        Args:
            left_content: Function to render left column content
            right_content: Function to render right column content
            column_ratio: Ratio between columns (left, right)
        """
        try:
            col1, col2 = st.columns(column_ratio)
            
            with col1:
                if left_content:
                    left_content()
            
            with col2:
                if right_content:
                    right_content()
                    
        except Exception as e:
            self.logger.error(f"Failed to render two-column layout: {str(e)}")
    
    def render_three_column_layout(self,
                                  left_content: Callable = None,
                                  center_content: Callable = None,
                                  right_content: Callable = None,
                                  column_ratio: tuple = (1, 2, 1)) -> None:
        """
        Render a three-column layout.
        
        Args:
            left_content: Function to render left column content
            center_content: Function to render center column content
            right_content: Function to render right column content
            column_ratio: Ratio between columns (left, center, right)
        """
        try:
            col1, col2, col3 = st.columns(column_ratio)
            
            with col1:
                if left_content:
                    left_content()
            
            with col2:
                if center_content:
                    center_content()
            
            with col3:
                if right_content:
                    right_content()
                    
        except Exception as e:
            self.logger.error(f"Failed to render three-column layout: {str(e)}")
    
    def render_tabs_layout(self, 
                          tab_config: Dict[str, Callable],
                          default_tab: Optional[str] = None) -> str:
        """
        Render a tabbed layout.
        
        Args:
            tab_config: Dictionary mapping tab names to content functions
            default_tab: Default selected tab
            
        Returns:
            Currently selected tab name
        """
        try:
            if not tab_config:
                return ""
            
            tab_names = list(tab_config.keys())
            
            # Create tabs
            tabs = st.tabs(tab_names)
            
            # Render each tab's content
            for i, (tab_name, content_func) in enumerate(tab_config.items()):
                with tabs[i]:
                    if content_func:
                        content_func()
            
            # Return the first tab name as default (Streamlit doesn't expose selected tab)
            return tab_names[0]
            
        except Exception as e:
            self.logger.error(f"Failed to render tabs layout: {str(e)}")
            return ""
    
    def render_expandable_section(self, 
                                title: str, 
                                content_func: Callable,
                                expanded: bool = False) -> None:
        """
        Render an expandable section.
        
        Args:
            title: Section title
            content_func: Function to render section content
            expanded: Whether section is expanded by default
        """
        try:
            with st.expander(title, expanded=expanded):
                if content_func:
                    content_func()
                    
        except Exception as e:
            self.logger.error(f"Failed to render expandable section '{title}': {str(e)}")
    
    def render_metric_cards(self, metrics: Dict[str, Dict[str, Any]], cols: int = 3) -> None:
        """
        Render metrics as cards in a grid layout.
        
        Args:
            metrics: Dictionary with metric data
            cols: Number of columns for the grid
        """
        try:
            if not metrics:
                return
            
            # Create columns for metrics
            metric_cols = st.columns(cols)
            
            for i, (metric_name, metric_data) in enumerate(metrics.items()):
                col_idx = i % cols
                
                with metric_cols[col_idx]:
                    value = metric_data.get('value', 'N/A')
                    delta = metric_data.get('delta')
                    help_text = metric_data.get('help', '')
                    
                    st.metric(
                        label=metric_name,
                        value=value,
                        delta=delta,
                        help=help_text
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to render metric cards: {str(e)}")
    
    def render_info_panel(self, 
                         title: str,
                         content: Dict[str, Any],
                         panel_type: str = "info") -> None:
        """
        Render an information panel.
        
        Args:
            title: Panel title
            content: Panel content dictionary
            panel_type: Type of panel (info, success, warning, error)
        """
        try:
            # Panel styling based on type
            panel_styles = {
                "info": "ℹ️",
                "success": "✅", 
                "warning": "⚠️",
                "error": "❌"
            }
            
            icon = panel_styles.get(panel_type, "📋")
            
            # Create container for the panel
            with st.container():
                st.markdown(f"### {icon} {title}")
                
                # Render content
                if isinstance(content, dict):
                    for key, value in content.items():
                        st.markdown(f"**{key}:** {value}")
                elif isinstance(content, str):
                    st.markdown(content)
                else:
                    st.write(content)
                    
        except Exception as e:
            self.logger.error(f"Failed to render info panel '{title}': {str(e)}")
    
    def render_loading_placeholder(self, message: str = "Loading...") -> None:
        """
        Render a loading placeholder.
        
        Args:
            message: Loading message
        """
        try:
            with st.empty():
                st.info(f"🔄 {message}")
                
        except Exception as e:
            self.logger.error(f"Failed to render loading placeholder: {str(e)}")
    
    def render_error_message(self, 
                           error_msg: str, 
                           details: Optional[str] = None,
                           show_details: bool = False) -> None:
        """
        Render an error message with optional details.
        
        Args:
            error_msg: Main error message
            details: Additional error details
            show_details: Whether to show details by default
        """
        try:
            st.error(f"❌ {error_msg}")
            
            if details and show_details:
                with st.expander("Error Details", expanded=False):
                    st.code(details)
                    
        except Exception as e:
            self.logger.error(f"Failed to render error message: {str(e)}")
    
    def render_footer(self) -> None:
        """Render application footer."""
        try:
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.markdown(
                    """
                    <div style='text-align: center; color: #666; font-size: 0.8em;'>
                        <p>🌍 Sky Globe - Powered by OpenWeatherMap API</p>
                        <p>Made with ❤️ using Streamlit and Pydeck</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        except Exception as e:
            self.logger.error(f"Failed to render footer: {str(e)}")
    
    def _render_default_sidebar(self) -> None:
        """Render default sidebar content."""
        st.sidebar.title("🌍 City Search")
        st.sidebar.info("Use the search components to explore weather data")
    
    def _render_default_main(self) -> None:
        """Render default main content."""
        st.title("🌍 Global Weather")
        st.info("Use the 3D globe to explore global weather patterns")
    
    def _render_debug_stats(self) -> None:
        """Render debug statistics."""
        try:
            with st.expander("🛠 Debug Stats", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Environment", config.environment)
                
                with col2:
                    st.metric("Debug Mode", config.is_debug())
                
                with col3:
                    st.metric("Cache TTL", f"{config.cache_ttl_weather}s")
                    
        except Exception as e:
            self.logger.error(f"Failed to render debug stats: {str(e)}")


# Global layout manager instance
layout_manager = LayoutManager()


# Convenience functions for common layouts
def setup_page(title: str = "Sky Globe - Global Weather") -> None:
    """Setup page configuration with custom title."""
    layout_manager.setup_page_config(title)


def render_header(show_stats: bool = False) -> None:
    """Render application header."""
    layout_manager.render_header(show_stats)


def render_main_layout(sidebar_content: Callable = None,
                      main_content: Callable = None,
                      sidebar_width: float = 0.3) -> None:
    """Render main application layout."""
    layout_manager.render_main_layout(sidebar_content, main_content, sidebar_width)


def render_footer() -> None:
    """Render application footer."""
    layout_manager.render_footer()