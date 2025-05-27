# Changelog

All notable changes to RunTracker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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