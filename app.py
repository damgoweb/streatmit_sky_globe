# -*- coding: utf-8 -*-
"""
Sky Globe - 世界の今の空
Main Streamlit application for real-time global weather visualization.
"""

import streamlit as st
import logging
from datetime import datetime
from typing import Dict, Any

# Import services
from src.business.geo_service import GeoService
from src.business.weather_service import WeatherService
from src.business.globe_service import GlobeService
from src.business.time_service import TimeService

# Import UI components
from src.ui.layouts import setup_page, render_header, render_main_layout, render_footer
from src.ui.components import (
    render_search_component, 
    render_weather_card, 
    render_settings_panel,
    render_globe_component,
    component_manager
)

# Import utilities
from src.utils.config import config


class SkyGlobeApp:
    """Main Sky Globe application class."""
    
    def __init__(self):
        """Initialize the Sky Globe application."""
        # Setup logging
        logging.basicConfig(
            level=logging.INFO if config.is_debug() else logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.geo_service = GeoService()
        self.weather_service = WeatherService()
        self.globe_service = GlobeService()
        self.time_service = TimeService()
        
        self.logger.info("Sky Globe application initialized")
    
    def run(self) -> None:
        """Run the main application."""
        try:
            # Setup page configuration
            setup_page("Sky Globe - 世界の今の空")
            
            # Initialize session state
            self._initialize_session_state()
            
            # Render main application
            self._render_application()
                
        except Exception as e:
            self.logger.error(f"Failed to run application: {str(e)}")
            st.error("❌ アプリケーションの起動に失敗しました")
            st.error(f"エラー詳細: {str(e)}")
            
            if config.is_debug():
                st.exception(e)
    
    def _initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        try:
            # Initialize default values if not exists
            defaults = {
                'selected_city': None,
                'current_weather': None,
                'app_settings': {
                    'temp_unit': 'C',
                    'wind_unit': 'ms',
                    'show_day_night': True,
                    'show_city_labels': True,
                    'auto_refresh': False,
                    'refresh_interval': 10
                },
                'last_refresh': None
            }
            
            for key, value in defaults.items():
                if key not in st.session_state:
                    st.session_state[key] = value
            
            # Set default city if none selected
            if st.session_state.selected_city is None:
                default_city = self.geo_service.get_city_by_name(config.DEFAULT_CITY)
                if default_city:
                    st.session_state.selected_city = default_city
                    self.logger.info(f"Set default city to {config.DEFAULT_CITY}")
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize session state: {str(e)}")
    
    def _render_application(self) -> None:
        """Render the main application interface."""
        try:
            # Render header
            render_header(show_stats=config.is_debug())
            
            # Main layout with sidebar and content
            render_main_layout(
                sidebar_content=self._render_sidebar,
                main_content=self._render_main_content,
                sidebar_width=0.35
            )
            
            # Render footer
            render_footer()
            
        except Exception as e:
            self.logger.error(f"Failed to render application: {str(e)}")
            st.error("アプリケーションの描画に失敗しました")
    
    def _render_sidebar(self) -> None:
        """Render the sidebar content."""
        try:
            # Search component
            selected_city = render_search_component(self.geo_service)
            
            # Update selected city if changed
            if selected_city and selected_city != st.session_state.selected_city:
                st.session_state.selected_city = selected_city
                st.session_state.current_weather = None  # Clear weather cache
                st.rerun()
            
            # Weather information for selected city
            if st.session_state.selected_city:
                self._render_weather_section()
            
            st.markdown("---")
            
            # Settings panel
            settings = render_settings_panel()
            if settings != st.session_state.app_settings:
                st.session_state.app_settings = settings
                st.rerun()
            
            st.markdown("---")
            
            # Status panel
            self._render_status_panel()
            
        except Exception as e:
            self.logger.error(f"Failed to render sidebar: {str(e)}")
            st.error("サイドバーの表示に失敗しました")
    
    def _render_weather_section(self) -> None:
        """Render weather information section."""
        try:
            city = st.session_state.selected_city
            if not city:
                return
            
            # Get or fetch weather data
            weather_data = st.session_state.current_weather
            
            if weather_data is None or self._should_refresh_weather():
                with st.spinner(f"{city.name_ja}の天気を取得中..."):
                    weather_data = self.weather_service.get_weather_for_city(city)
                
                if weather_data:
                    st.session_state.current_weather = weather_data
                    st.session_state.last_refresh = datetime.now()
                    self.logger.info(f"Weather data refreshed for {city.name_en}")
                else:
                    st.error(f"❌ {city.name_ja}の天気データを取得できませんでした")
                    return
            
            # Render weather card
            if weather_data:
                temp_unit = st.session_state.app_settings.get('temp_unit', 'C')
                render_weather_card(weather_data, temp_unit)
                
        except Exception as e:
            self.logger.error(f"Failed to render weather section: {str(e)}")
            st.error("天気情報の表示に失敗しました")
    
    def _render_main_content(self) -> None:
        """Render the main content area."""
        try:
            st.markdown("### 🌍 リアルタイム地球儀")
            
            # Load cities for globe display
            cities = self._get_cities_for_display()
            if not cities:
                st.error("都市データの読み込みに失敗しました")
                return
            
            # Get weather data for visible cities
            weather_data = self._get_weather_data_for_cities(cities[:10])  # Limit for performance
            
            # Render globe component
            render_globe_component(
                cities=cities,
                weather_data=weather_data,
                selected_city=st.session_state.selected_city,
                settings=st.session_state.app_settings
            )
            
            # Render globe information panel
            self._render_globe_info_panel(len(cities), len(weather_data))
            
        except Exception as e:
            self.logger.error(f"Failed to render main content: {str(e)}")
            st.error("メインコンテンツの表示に失敗しました")
    
    def _render_status_panel(self) -> None:
        """Render status panel."""
        try:
            with st.expander("📊 システム状況", expanded=False):
                services = {
                    'weather_service': self.weather_service,
                    'geo_service': self.geo_service
                }
                component_manager.render_status_panel(services)
            
            # Help panel
            with st.expander("❓ ヘルプ", expanded=False):
                component_manager.render_help_panel()
                
        except Exception as e:
            self.logger.error(f"Failed to render status panel: {str(e)}")
    
    def _render_globe_info_panel(self, total_cities: int, weather_cities: int) -> None:
        """Render information panel about the globe display."""
        try:
            with st.expander("ℹ️ 地球儀について", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("表示都市数", total_cities)
                
                with col2:
                    st.metric("天気データ", weather_cities)
                
                with col3:
                    if st.session_state.selected_city:
                        local_time = self.time_service.get_local_time(
                            st.session_state.selected_city.timezone
                        )
                        if local_time:
                            st.metric("現地時刻", local_time.strftime("%H:%M"))
                
                st.markdown("""
                **操作方法:**
                - マウスドラッグ: 地球儀を回転
                - ホイール: ズームイン・アウト
                - 都市マーカー: クリックで詳細表示
                """)
                
        except Exception as e:
            self.logger.error(f"Failed to render globe info panel: {str(e)}")
    
    def _get_cities_for_display(self) -> list:
        """Get list of cities for globe display."""
        try:
            if self.geo_service.cities_df is not None:
                cities = []
                for _, row in self.geo_service.cities_df.iterrows():
                    try:
                        city = self.geo_service.get_city_by_id(row['id'])
                        if city:
                            cities.append(city)
                    except Exception:
                        continue
                
                self.logger.info(f"Loaded {len(cities)} cities for display")
                return cities
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get cities for display: {str(e)}")
            return []
    
    def _get_weather_data_for_cities(self, cities: list) -> Dict[int, Any]:
        """Get weather data for a list of cities."""
        try:
            weather_data = {}
            
            # Limit requests to avoid API rate limits
            max_requests = min(len(cities), 5)
            
            for i, city in enumerate(cities[:max_requests]):
                try:
                    if i > 0:  # Add delay between requests
                        import time
                        time.sleep(0.5)
                    
                    weather = self.weather_service.get_weather_for_city(city)
                    if weather:
                        weather_data[city.id] = weather
                        
                except Exception as e:
                    self.logger.warning(f"Failed to get weather for {city.name_en}: {str(e)}")
                    continue
            
            self.logger.info(f"Retrieved weather data for {len(weather_data)} cities")
            return weather_data
            
        except Exception as e:
            self.logger.error(f"Failed to get weather data for cities: {str(e)}")
            return {}
    
    def _should_refresh_weather(self) -> bool:
        """Check if weather data should be refreshed."""
        try:
            if st.session_state.last_refresh is None:
                return True
            
            # Check if enough time has passed since last refresh
            refresh_interval = st.session_state.app_settings.get('refresh_interval', 10)
            time_since_refresh = (datetime.now() - st.session_state.last_refresh).total_seconds()
            
            return time_since_refresh > (refresh_interval * 60)
            
        except Exception:
            return True


def main():
    """Main entry point for the application."""
    try:
        # Create and run the application
        app = SkyGlobeApp()
        app.run()
        
    except Exception as e:
        # Last resort error handling
        st.error("🚨 アプリケーションで重大なエラーが発生しました")
        st.error(f"エラー: {str(e)}")
        
        # Show basic information in case of total failure
        st.markdown("""
        ## Sky Globe - 世界の今の空
        
        申し訳ございませんが、アプリケーションの初期化に失敗しました。
        
        **考えられる原因:**
        - APIキーが正しく設定されていない
        - 必要なファイルが見つからない  
        - ネットワーク接続の問題
        
        **解決方法:**
        1. `.streamlit/secrets.toml`にOpenWeatherMap APIキーが設定されていることを確認
        2. 必要な依存関係がインストールされていることを確認 (`pip install -r requirements.txt`)
        3. ページを更新して再試行
        """)


if __name__ == "__main__":
    main()