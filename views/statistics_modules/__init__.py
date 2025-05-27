"""
Statistics modules package for running analytics dashboard
"""

# Import main functions for easy access
from .data_processing import (
    preprocess_dataframe,
    filter_data_by_time_period,
    calculate_key_metrics,
    detect_workout_type,
    get_workout_type_style
)

from .metric_cards import (
    create_metric_card,
    create_all_metric_cards,
    get_trend_indicator
)

from .styles import get_statistics_css

from .chart_creators import (
    create_distance_chart,
    create_pace_trend_chart,
    create_heart_rate_chart,
    create_pace_distribution_chart,
    create_cadence_chart,
    create_elevation_chart,
    create_elapsed_time_chart,
    create_run_frequency_chart,
    create_yearly_cumulative_chart,
    create_correlation_chart,
    create_heart_rate_zones_chart,
    create_monthly_volume_chart
)

from .insights import (
    generate_insights,
    get_no_insights_message
)

__all__ = [
    # Data processing
    'preprocess_dataframe',
    'filter_data_by_time_period',
    'calculate_key_metrics',
    'detect_workout_type',
    'get_workout_type_style',
    
    # Metric cards
    'create_metric_card',
    'create_all_metric_cards',
    'get_trend_indicator',
    
    # Styles
    'get_statistics_css',
    
    # Chart creators
    'create_distance_chart',
    'create_pace_trend_chart',
    'create_heart_rate_chart',
    'create_pace_distribution_chart',
    'create_cadence_chart',
    'create_elevation_chart',
    'create_elapsed_time_chart',
    'create_run_frequency_chart',
    'create_yearly_cumulative_chart',
    'create_correlation_chart',
    'create_heart_rate_zones_chart',
    'create_monthly_volume_chart',
    
    # Insights
    'generate_insights',
    'get_no_insights_message'
] 