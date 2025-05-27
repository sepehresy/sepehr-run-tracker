"""
CSS styles for the running statistics dashboard with mobile-first responsive design
"""

def get_statistics_css():
    """Return the complete CSS styles for the statistics page with proper contrast and mobile responsiveness"""
    return """
    <style>
    /* ==============================================
       DESIGN SYSTEM RULES - NEVER VIOLATE THESE!
       ============================================== */
    
    /* CONTRAST RULES:
       - Text on light backgrounds: minimum #374151 (dark gray)
       - Text on dark backgrounds: minimum #f9fafb (light gray)
       - Interactive elements: minimum 4.5:1 contrast ratio
       - Large text (18px+): minimum 3:1 contrast ratio
    */
    
    /* MOBILE-FIRST RULES:
       - Design for 320px width first
       - Use rem units for scalability
       - Touch targets minimum 44px
       - Readable font sizes (16px+ on mobile)
    */
    
    /* ==============================================
       GLOBAL RESET AND BASE STYLES
       ============================================== */
    
    .main .block-container {
        padding: 0.5rem;
        max-width: 100%;
        margin: 0 auto;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%) !important;
        min-height: 100vh;
    }
    
    /* Mobile-first typography */
    * {
        box-sizing: border-box;
    }
    
    /* Dark theme for main app */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%) !important;
        color: #f8fafc !important;
    }
    
    /* ==============================================
       HEADER SECTION
       ============================================== */
    
    .stats-header {
        text-align: center;
        margin-bottom: 1.5rem;
        padding: 1.5rem;
        background: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        box-shadow: 
            0 4px 6px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
    
    .stats-title {
        font-size: 1.75rem; /* Mobile first */
        font-weight: 700;
        color: #f8fafc !important; /* High contrast on dark */
        margin: 0;
        letter-spacing: -0.025em;
        line-height: 1.2;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
    
    .stats-subtitle {
        font-size: 0.875rem;
        color: #cbd5e1 !important; /* Good contrast on dark */
        margin: 0.5rem 0 0 0;
        font-weight: 500;
    }
    
    /* ==============================================
       METRIC CARDS - MOBILE FIRST DESIGN
       ============================================== */
    
    .metric-grid {
        display: grid;
        gap: 0.75rem;
        margin: 1rem 0;
        /* Mobile: Single compact card */
        grid-template-columns: 1fr;
    }
    
    /* Mobile: Compact summary card */
    .metric-summary-card {
        background: rgba(30, 41, 59, 0.9) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 
            0 4px 6px rgba(0, 0, 0, 0.3),
            0 1px 3px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        color: #f8fafc !important;
    }
    
    .metric-summary-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 1rem;
        margin-top: 1rem;
    }
    
    .metric-summary-item {
        text-align: center;
        padding: 0.75rem;
        background: rgba(51, 65, 85, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(148, 163, 184, 0.1);
        transition: all 0.2s ease;
    }
    
    .metric-summary-item:hover {
        background: rgba(71, 85, 105, 0.7);
        transform: translateY(-2px);
        border-color: rgba(148, 163, 184, 0.3);
    }
    
    .metric-summary-icon {
        font-size: 1.25rem;
        margin-bottom: 0.25rem;
        display: block;
        filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
    }
    
    .metric-summary-label {
        font-size: 0.625rem;
        font-weight: 600;
        color: #cbd5e1 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
        line-height: 1.2;
    }
    
    .metric-summary-value {
        font-size: 0.875rem;
        font-weight: 700;
        color: #f8fafc !important;
        line-height: 1.1;
        font-variant-numeric: tabular-nums;
    }
    
    /* Desktop: Individual cards */
    .metric-card {
        /* Beautiful dark card design with proper contrast */
        background: rgba(30, 41, 59, 0.9) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-radius: 16px;
        padding: 1.25rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 
            0 4px 6px rgba(0, 0, 0, 0.3),
            0 1px 3px rgba(0, 0, 0, 0.2),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        position: relative;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        text-align: center;
        min-width: 44px;
        cursor: pointer;
        color: #f8fafc !important;
        overflow: hidden;
        /* Hide individual cards on mobile */
        display: none;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6, #06b6d4, #10b981);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .metric-card:hover::before {
        opacity: 1;
    }
    
    .metric-card:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 
            0 20px 25px rgba(0, 0, 0, 0.4),
            0 10px 10px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
        background: rgba(51, 65, 85, 0.95) !important;
    }
    
    .metric-card:active {
        transform: translateY(-2px) scale(1.01);
    }
    
    .metric-icon {
        font-size: 1.75rem;
        margin-bottom: 0.5rem;
        display: block;
        line-height: 1;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover .metric-icon {
        transform: scale(1.1);
    }
    
    .metric-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
        gap: 0.25rem;
    }
    
    .metric-title {
        font-size: 0.75rem;
        font-weight: 600;
        color: #cbd5e1 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.25rem;
        line-height: 1.2;
    }
    
    .metric-value {
        font-size: 1.125rem;
        font-weight: 700;
        color: #f8fafc !important;
        line-height: 1.1;
        margin-bottom: 0.25rem;
        font-variant-numeric: tabular-nums;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    .metric-change {
        font-size: 0.75rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.25rem;
        margin-top: 0.25rem;
        padding: 0.25rem 0.5rem;
        border-radius: 12px;
        background: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(10px);
    }
    
    .metric-change.positive {
        color: #34d399 !important;
        background: rgba(52, 211, 153, 0.2);
    }
    
    .metric-change.negative {
        color: #f87171 !important;
        background: rgba(248, 113, 113, 0.2);
    }
    
    .metric-change.neutral {
        color: #94a3b8 !important;
        background: rgba(148, 163, 184, 0.2);
    }
    
    /* ==============================================
       SECTION HEADERS
       ============================================== */
    
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f8fafc !important;
        margin: 2rem 0 1rem 0;
        text-align: center;
        border-bottom: 2px solid rgba(148, 163, 184, 0.3);
        padding: 1rem;
        background: rgba(15, 23, 42, 0.8);
        backdrop-filter: blur(20px);
        border-radius: 12px 12px 0 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
    }
    
    /* ==============================================
       CHART CONTAINERS
       ============================================== */
    
    .chart-container {
        background: rgba(30, 41, 59, 0.9) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 
            0 4px 6px rgba(0, 0, 0, 0.3),
            0 1px 3px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }
    
    .chart-container:hover {
        box-shadow: 
            0 10px 15px rgba(0, 0, 0, 0.4),
            0 4px 6px rgba(0, 0, 0, 0.3);
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    .chart-title {
        font-size: 1rem;
        font-weight: 600;
        color: #f8fafc !important;
        margin: 0 0 1rem 0;
        text-align: center;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* ==============================================
       WORKOUT TYPE LEGEND
       ============================================== */
    
    .workout-legend {
        background: rgba(15, 23, 42, 0.9) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .legend-title {
        font-size: 1rem;
        font-weight: 600;
        color: #f8fafc !important;
        margin-bottom: 0.75rem;
        text-align: center;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    .legend-items {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.5rem;
    }
    
    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
        color: #cbd5e1 !important;
        font-weight: 500;
        padding: 0.5rem;
        background: rgba(51, 65, 85, 0.5);
        border-radius: 8px;
        transition: all 0.2s ease;
        border: 1px solid rgba(148, 163, 184, 0.1);
    }
    
    .legend-item:hover {
        background: rgba(71, 85, 105, 0.7);
        transform: translateY(-1px);
        border-color: rgba(148, 163, 184, 0.3);
    }
    
    /* ==============================================
       INSIGHTS SECTION
       ============================================== */
    
    .insight-card {
        background: rgba(30, 41, 59, 0.9) !important;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-left: 4px solid #3b82f6;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .insight-card:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        border-left-color: #60a5fa;
    }
    
    .insight-card p {
        color: #cbd5e1 !important;
        font-size: 0.875rem;
        line-height: 1.5;
        margin: 0;
    }
    
    .insight-card strong {
        color: #f8fafc !important;
        font-weight: 600;
    }
    
    /* ==============================================
       RESPONSIVE BREAKPOINTS
       ============================================== */
    
    /* Small tablets: 480px and up */
    @media (min-width: 30rem) {
        .main .block-container {
            padding: 1rem;
        }
        
        .stats-title {
            font-size: 2rem;
        }
        
        /* Still use compact card but with better spacing */
        .metric-summary-grid {
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
        }
        
        .metric-summary-item {
            padding: 1rem;
        }
        
        .metric-summary-value {
            font-size: 1rem;
        }
        
        .legend-items {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    
    /* Tablets: 768px and up - Switch to individual cards */
    @media (min-width: 48rem) {
        .main .block-container {
            padding: 1.5rem;
            max-width: 1200px;
        }
        
        .stats-title {
            font-size: 2.5rem;
        }
        
        /* Hide compact card, show individual cards */
        .metric-summary-card {
            display: none;
        }
        
        .metric-card {
            display: flex !important;
        }
        
        .metric-grid {
            grid-template-columns: repeat(8, 1fr);
            gap: 1rem;
        }
        
        .metric-card {
            min-height: 120px;
            padding: 1.25rem;
        }
        
        .metric-value {
            font-size: 1.25rem;
        }
        
        .metric-icon {
            font-size: 1.5rem;
        }
        
        .legend-items {
            grid-template-columns: repeat(7, 1fr);
        }
        
        .chart-container {
            padding: 1.5rem;
        }
    }
    
    /* Desktop: 1024px and up */
    @media (min-width: 64rem) {
        .metric-card:hover {
            transform: translateY(-6px) scale(1.03);
        }
        
        .metric-value {
            font-size: 1.5rem;
        }
        
        .metric-icon {
            font-size: 1.75rem;
        }
    }
    
    /* Large desktop: 1280px and up */
    @media (min-width: 80rem) {
        .main .block-container {
            max-width: 1400px;
        }
    }
    
    /* ==============================================
       ACCESSIBILITY IMPROVEMENTS
       ============================================== */
    
    /* Focus states for keyboard navigation */
    .metric-card:focus,
    .metric-summary-item:focus {
        outline: 2px solid #60a5fa;
        outline-offset: 2px;
    }
    
    /* Reduced motion for users who prefer it */
    @media (prefers-reduced-motion: reduce) {
        .metric-card,
        .metric-summary-item {
            transition: none;
        }
        
        .metric-card:hover,
        .metric-summary-item:hover {
            transform: none;
        }
        
        .metric-icon {
            transition: none;
        }
        
        .metric-card:hover .metric-icon {
            transform: none;
        }
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        .metric-card,
        .metric-summary-card {
            border-width: 3px !important;
            border-color: #ffffff !important;
        }
        
        .metric-title,
        .metric-value,
        .metric-summary-label,
        .metric-summary-value {
            color: #ffffff !important;
        }
        
        .section-header,
        .chart-title {
            color: #ffffff !important;
        }
    }
    
    /* ==============================================
       FORCE OVERRIDE STREAMLIT STYLES
       ============================================== */
    
    /* Override any light theme styles that might interfere */
    .stApp [data-testid="stMetricValue"],
    .stApp [data-testid="stMetricLabel"],
    .stApp .metric-card *,
    .stApp .metric-summary-card *,
    .stApp .chart-container *,
    .stApp .section-header,
    .stApp .stats-title,
    .stApp .stats-subtitle {
        color: inherit !important;
    }
    
    /* Ensure proper backgrounds are maintained */
    .stApp .metric-card,
    .stApp .metric-summary-card,
    .stApp .chart-container,
    .stApp .insight-card {
        background: inherit !important;
    }
    
    /* Override Streamlit's default light theme */
    .stApp > div {
        background: transparent !important;
    }
    
    /* ==============================================
       PRINT STYLES
       ============================================== */
    
    @media print {
        .metric-card,
        .metric-summary-card {
            break-inside: avoid;
            box-shadow: none;
            border: 1px solid #000;
            background: #ffffff !important;
        }
        
        .metric-grid {
            grid-template-columns: repeat(4, 1fr);
        }
        
        .metric-title,
        .metric-value,
        .metric-summary-label,
        .metric-summary-value,
        .section-header,
        .chart-title {
            color: #000000 !important;
        }
    }
    </style>
    """