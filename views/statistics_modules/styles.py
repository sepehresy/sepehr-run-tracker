"""
CSS styles for the running statistics dashboard
"""

def get_statistics_css():
    """Return the complete CSS styles for the statistics page"""
    return """
    <style>
    /* Global reset and base styles */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    
    /* Statistics page specific styles */
    .stats-header {
        text-align: center;
        margin-bottom: 2rem;
        padding: 0;
    }
    
    .stats-title {
        font-size: 2.5rem;
        font-weight: 300;
        color: #1f2937;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .stats-subtitle {
        font-size: 1rem;
        color: #6b7280;
        margin: 0.5rem 0 0 0;
        font-weight: 400;
    }
    
    /* Enhanced Metric Cards - 8 Columns in One Row */
    .metric-grid {
        margin: 1.5rem 0;
        display: grid;
        grid-template-columns: repeat(8, 1fr);
        gap: 1rem;
        justify-content: center;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 0.75rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 4px 6px -1px rgba(0, 0, 0, 0.1),
            0 2px 4px -1px rgba(0, 0, 0, 0.06),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
        cursor: pointer;
        height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        align-items: center;
        text-align: center;
    }
    
    .metric-card:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: #3b82f6;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4, #10b981);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .metric-card:hover::before {
        opacity: 1;
    }
    
    .metric-header {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    
    .metric-icon {
        font-size: 1.25rem;
        margin-bottom: 0.25rem;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
    }
    
    .metric-card:hover .metric-icon {
        transform: scale(1.1);
    }
    
    .metric-main {
        flex: 1;
    }
    
    .metric-value-container {
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 1rem;
        font-weight: 700;
        color: #1a202c;
        line-height: 1;
        font-variant-numeric: tabular-nums;
        margin-bottom: 0.125rem;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    .metric-unit {
        font-size: 0.625rem;
        color: #718096;
        font-weight: 500;
        margin-left: 0.125rem;
    }
    
    .metric-label {
        font-size: 0.5rem;
        color: #4a5568;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        line-height: 1.2;
        margin-bottom: 0.125rem;
    }
    
    .metric-subtitle {
        font-size: 0.4rem;
        color: #a0aec0;
        font-weight: 400;
        line-height: 1.2;
        opacity: 0.8;
    }
    
    /* Goal Progress */
    .goal-progress {
        margin: 1rem 0 0.5rem 0;
    }
    
    .progress-bar {
        width: 100%;
        height: 6px;
        background: #e5e7eb;
        border-radius: 3px;
        overflow: hidden;
        margin-bottom: 0.5rem;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #10b981, #3b82f6);
        border-radius: 3px;
        transition: width 0.8s ease;
        position: relative;
    }
    
    .progress-fill::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .progress-text {
        font-size: 0.75rem;
        color: #6b7280;
        font-weight: 500;
    }
    
    /* Trend Indicators */
    .metric-change {
        position: absolute;
        top: 0.25rem;
        right: 0.25rem;
        font-size: 0.625rem;
        padding: 0.0625rem 0.125rem;
        border-radius: 4px;
        font-weight: 600;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .trend-icon {
        font-size: 1rem;
    }
    
    .metric-change.positive {
        color: #059669;
    }
    
    .metric-change.negative {
        color: #dc2626;
    }
    
    .metric-change.neutral {
        color: #6b7280;
    }
    
    .trend-tooltip {
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%);
        background: #1f2937;
        color: white;
        padding: 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        white-space: nowrap;
        opacity: 0;
        pointer-events: none;
        transition: opacity 0.3s ease;
        margin-bottom: 0.5rem;
    }
    
    .metric-change:hover .trend-tooltip {
        opacity: 1;
    }
    
    /* Section headers */
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1f2937;
        margin: 3rem 0 1.5rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
        position: relative;
    }
    
    .section-header::after {
        content: '';
        position: absolute;
        bottom: -2px;
        left: 0;
        width: 60px;
        height: 2px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    }
    
    /* Chart containers */
    .chart-container {
        background: #ffffff;
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .chart-container:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .chart-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #1f2937;
        margin: 0 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Time period selector */
    .time-selector {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin: 2rem 0;
        flex-wrap: wrap;
    }
    
    .time-button {
        padding: 0.75rem 1.5rem;
        border: 2px solid #e5e7eb;
        border-radius: 12px;
        background: #ffffff;
        color: #6b7280;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.875rem;
        position: relative;
        overflow: hidden;
    }
    
    .time-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(59, 130, 246, 0.1), transparent);
        transition: left 0.5s ease;
    }
    
    .time-button:hover::before {
        left: 100%;
    }
    
    .time-button:hover {
        border-color: #3b82f6;
        color: #3b82f6;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    }
    
    .time-button.active {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        color: #ffffff;
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    /* Insights section */
    .insight-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-left: 4px solid #0ea5e9;
        border-radius: 0 12px 12px 0;
        padding: 1.25rem;
        margin: 1rem 0;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        color: #1f2937 !important;
    }
    
    .insight-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s ease;
    }
    
    .insight-card:hover::before {
        left: 100%;
    }
    
    .insight-card:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.15);
    }
    
    .insight-card strong {
        color: #0f172a !important;
        font-weight: 700;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .metric-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
        
        .metric-card {
            padding: 1.25rem;
        }
        
        .metric-value {
            font-size: 2rem;
        }
        
        .metric-icon {
            font-size: 2rem;
        }
        
        .stats-title {
            font-size: 2rem;
        }
        
        .time-button {
            padding: 0.5rem 1rem;
            font-size: 0.8rem;
        }
    }
    
    @media (max-width: 480px) {
        .metric-grid {
            grid-template-columns: 1fr;
        }
        
        .metric-header {
            flex-direction: column;
            align-items: center;
            text-align: center;
            gap: 0.5rem;
        }
        
        .metric-value {
            font-size: 1.75rem;
        }

    }
    
    /* Hide Streamlit elements */
    .stPlotlyChart > div {
        border-radius: 20px;
        overflow: hidden;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #cbd5e1, #94a3b8);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #94a3b8, #64748b);
    }
    
    /* Loading animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .metric-card {
        animation: fadeInUp 0.6s ease-out;
    }
    
    .chart-container {
        animation: fadeInUp 0.8s ease-out;
    }
    
    /* Workout Type Legend */
    .workout-legend {
        background: rgba(30, 30, 30, 0.95);
        backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .legend-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .legend-items {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 0.75rem;
        justify-items: center;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
        color: #ffffff;
        font-weight: 500;
    }
    
    .legend-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        background: rgba(255, 255, 255, 0.15);
    }
    
    </style>
    """