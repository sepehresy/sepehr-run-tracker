# Changelog

All notable changes to RunTracker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2025-01-28

### 🚀 Major Feature: Modern Activities View

#### ✨ New Activities Dashboard
- **Complete Redesign**: Modern card-based activity view with enhanced data visualization
- **Streamlined Table**: Simplified activity table showing only essential columns (Date, Name, Sport Type, Type, Workout Type, Description, Distance, Pace, Time)
- **Intelligent Column Management**: Hidden non-essential columns while preserving all data for detailed views

#### 🎯 Activity Detail Cards
- **Activity Header Card**: Comprehensive activity summary with name, date, sport type, workout type, and all key metrics
- **Performance Analysis Card**: Advanced metrics including power analysis, performance ratings, training load, elevation analysis
- **Dynamic Content**: Cards automatically populate with available data, gracefully handling missing values

#### 📊 Enhanced Lap Analysis
- **Dual-Chart System**: 
  - Top chart (67% height): Variable-width pace bars proportional to lap distance with color-coded performance
  - Bottom chart (33% height): Heart rate and power trends with dual y-axes
- **Complete Data Extraction**: Parses lap details to extract pace, time, HR, cadence, power, and elevation gain
- **Comprehensive Table**: Lap breakdown with all available metrics per lap

#### 📈 New Horizontal Lap Chart
- **Right Sidebar Chart**: Horizontal bar chart (800px height) showing pace comparison across all laps
- **Performance Color Coding**: Green (fast), blue (medium), red (slow) bars based on relative performance
- **Inline Metrics**: Pace, heart rate, and elevation displayed directly alongside each bar (15px font)
- **Average Pace Reference**: Dashed red line showing overall average pace

#### 🗺️ Improved Route Visualization
- **Terrain View**: Switched from dark theme to topographical terrain view for better route understanding
- **Clean Design**: Removed header cards for streamlined map display
- **Enhanced Markers**: Clear start (green) and finish (red) markers with route line visualization

### 🛠️ Technical Improvements

#### 🔧 Robust Data Handling
- **Safe Float Conversion**: Added `safe_float_convert()` function to handle 'N/A', null, and invalid values
- **Error Prevention**: Eliminated "could not convert string to float" errors throughout the application
- **Data Integrity**: Preserved all original data while controlling display presentation

#### 📱 Responsive Layout
- **Two-Column Design**: Left column (2/3 width) for main content, right column (1/3 width) for secondary info
- **Mobile-First**: Responsive design that works across all device sizes
- **Modern CSS**: Glass-morphism effects, dark theme, and enhanced visual hierarchy

#### 🎨 UI/UX Enhancements
- **Card-Based Design**: Modern card system with hover effects and shadows
- **Color-Coded Performance**: Intuitive color schemes for quick performance assessment
- **Clean Information Architecture**: Logical flow from activity selection to detailed analysis

### 🧹 Code Quality & Cleanup
- **File Organization**: Moved `layout_designer.py` to docs folder
- **Removed Debug Files**: Cleaned up 7+ temporary debugging files (`check_columns.py`, `debug_selection.py`, etc.)
- **Optimized Imports**: Consolidated and cleaned import statements
- **Enhanced Documentation**: Comprehensive inline documentation for all new functions

### 🐛 Bug Fixes
- **Activity Selection**: Fixed activity selection and data flow between table and detail views
- **Data Type Errors**: Resolved float conversion errors with robust error handling
- **Chart Rendering**: Fixed Plotly chart configuration and annotation positioning
- **Table Display**: Corrected column visibility while preserving underlying data

### 📊 Data Processing Improvements
- **Lap Data Parsing**: Enhanced regex patterns to extract all available lap metrics
- **Flexible Format Support**: Support for various data formats (decimal HR, cadence, elevation)
- **Missing Data Handling**: Graceful degradation when data is not available

## [1.4.0] - 2025-01-27

### 🎨 UI/UX Improvements
- **Enhanced Dark Theme**: Updated statistics view with darker background colors for better visual hierarchy
- **Background Customization**: Changed main background to dark grey (#111827) for improved visual comfort
- **Component Styling**: Updated all metric cards, chart containers, and UI components with darker, more cohesive color scheme

### 🗂️ Project Organization
- **Documentation Restructure**: Created `docs/` folder and moved all test files and design documentation
- **Cleaner Root Directory**: Organized project structure by moving test files, design guides, and documentation to dedicated folder

### 🔧 Bug Fixes & Code Quality
- **Removed AI Analysis View**: Eliminated unused AI analysis feature that was not providing value
- **Fixed Import Errors**: Corrected race planning import path issues
- **Resolved Syntax Errors**: Fixed indentation problems in pace calculator and statistics modules
- **Error Handling**: Fixed UnboundLocalError in workout type detection function

### 📁 Files Moved to `docs/` Folder
- Test files: `test_pace_calculator_ui.py`, `validate_ui.py`, `test_ui_responsiveness.py`, `test_pace_fix.py`
- Documentation: `DESIGN_SYSTEM.md`, `MOBILE_TESTING_GUIDE.md`, `MODULAR_STRUCTURE.md`
- Test results: `PACE_CALCULATOR_UI_TEST_RESULTS.md`, `PACE_CALCULATOR_MOBILE_TEST.md`, `QUICK_MOBILE_TEST.md`, `SIMPLE_PACE_CALCULATOR.md`

### 🎯 Navigation Improvements
- **Simplified Menu**: Removed "🧠 AI Analysis" from sidebar navigation
- **Cleaner Interface**: Streamlined user experience by removing non-functional features

## [1.0.0] - 2025-05-27

### 🎉 Initial Release

#### ✨ Added
- **Statistics Dashboard** with mobile-optimized responsive design
- **Pace Calculator** with ultra-compact 2-row layout
- **Activities View** for workout data management
- **Fatigue Analysis** with training load metrics
- **Race Planning** module with AI integration
- **Runner Profile** management
- **Dark Theme** with glass-morphism UI design

#### 🏃‍♂️ Core Features
- **Statistics Dashboard**:
  - 8 key performance metrics (distance, runs, time, pace, heart rate, training load, elevation)
  - Time-based filtering (7 days, 30 days, 90 days, 1 year, all time)
  - Multiple aggregation views (daily, weekly, monthly, yearly)
  - Mobile compact view (single summary card) vs desktop individual cards
  - Performance trend charts with Plotly visualizations
  - Workout type detection and classification
  
- **Pace Calculator**:
  - Ultra-compact 2-row design (75% space reduction from original)
  - Row 1: Enter pace → get finish times for 5K, 10K, Half Marathon, Marathon
  - Row 2: Enter finish times → get calculated paces
  - Static reference table with common paces (4:00-10:00/km)
  - Mobile-responsive (4→2 columns on mobile screens)
  
- **Data Processing**:
  - Time parsing for multiple formats (MM:SS:00, HH:MM:SS, MM:SS)
  - Pace conversion between min:sec and decimal formats
  - Workout type detection based on activity names and characteristics
  - Training load calculation using distance and intensity factors

#### 🎨 Mobile-First Design
- **Responsive Breakpoints**: 30rem, 48rem, 64rem, 80rem
- **Touch Targets**: Minimum 44px for mobile accessibility
- **Typography**: Optimized font sizes (minimum 10px for compact layouts)
- **Layout**: Progressive enhancement from mobile to desktop
- **Color Scheme**: Dark gradient background (#0f172a to #334155)
- **Cards**: Glass-morphism with backdrop blur effects

#### 🛠️ Technical Implementation
- **Frontend**: Streamlit with custom CSS/HTML
- **Data Processing**: Pandas, NumPy for data manipulation
- **Visualizations**: Plotly for interactive charts
- **Authentication**: User login system with session management
- **Data Storage**: GitHub Gist integration for data persistence

#### 📱 Mobile Optimizations
- **Statistics Cards**: Compact summary card for mobile, individual cards for desktop
- **Pace Calculator**: Reduced padding and margins for ultra-compact layout
- **Touch Interface**: Enhanced mobile interaction experience
- **Responsive Grid**: Adaptive column layouts based on screen size

### 🐛 Bug Fixes
- Fixed pace data processing to show realistic running pace values
- Resolved time parsing issues for accurate workout duration calculation
- Enhanced workout type detection algorithm for better classification
- Improved mobile layout rendering consistency

### 📚 Documentation
- Comprehensive README.md with setup instructions
- CHANGELOG.md for version tracking
- CONTRIBUTING.md with development guidelines
- LICENSE file (MIT License)
- Requirements.txt with all dependencies 