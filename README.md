# 🏃‍♂️ RunTracker

**🤖 AI-POWERED Running Analytics & Training Plans** 

**Your intelligent running companion** - A comprehensive running analytics dashboard built with Streamlit that transforms your training data into actionable insights using **artificial intelligence**.

## 🧠 **AI-Powered Features**
- **🎯 AI Training Plan Generation** - Personalized workout schedules created by advanced AI
- **📊 AI Run Analysis** - Intelligent insights and recommendations from your training data
- **🔮 AI Performance Predictions** - Smart forecasting for your running goals
- **💡 AI Coaching Tips** - Personalized advice based on your training patterns

![RunTracker Login](screenshots/login.png)

## ✨ Features

### 📊 **AI-Enhanced Analytics Dashboard**
Transform your running data into beautiful, interactive visualizations with **AI-powered insights** and mobile-optimized responsive design.

![Running Analytics Dashboard](screenshots/analytics-dashboard.png)

**🤖 AI-Enhanced Metrics:**
- **Smart Performance Analysis** - AI identifies trends and patterns in your data
- **Intelligent Workout Classification** - AI automatically categorizes your runs
- **Predictive Training Load** - AI calculates optimal training intensity
- **Adaptive Time Filtering** - 7 days to All Time with AI recommendations
- **Smart Aggregation Views** - Daily, Weekly, Monthly, Yearly with AI insights

### ⚡ **Ultra-Compact Pace Calculator**
Calculate race times and paces with an efficient 2-row design that maximizes screen space.

**Calculator Features:**
- Row 1: Enter pace → get finish times for 5K, 10K, Half Marathon, Marathon
- Row 2: Enter finish times → get calculated paces
- Static reference table with common paces (4:00-10:00/km)
- Mobile-responsive design (4→2 columns on mobile)
- 75% space reduction from traditional calculators

### 📊 **Activities Management**
Comprehensive workout data management and visualization system.

**Activity Features:**
- Workout data import and processing
- Performance metrics calculation
- Activity history and trends
- Data export capabilities

### 📉 **AI-Powered Fatigue Analysis**
Monitor your training load and recovery status with **AI-driven insights** and advanced metrics.

**🤖 AI Analysis Features:**
- **Smart Training Load** - AI calculates optimal training intensity
- **Intelligent Recovery Tracking** - AI predicts when you need rest
- **AI Performance Trends** - Machine learning identifies improvement patterns
- **Personalized Recommendations** - AI coaching advice based on your data

### 🎯 **AI-Powered Race Planning**
**Advanced artificial intelligence** creates personalized training plans tailored to your running goals and current fitness level.

**🤖 AI Planning Features:**
- **Smart Training Plans** - AI analyzes your data to create optimal workout schedules
- **Multiple Race Distances** - 5K, 10K, Half Marathon, Marathon support
- **Adaptive Scheduling** - AI adjusts plans based on your progress and performance
- **Intelligent Recommendations** - AI-driven coaching advice and training tips
- **Performance Forecasting** - AI predicts your race times and goal achievement

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sepehr-run-tracker.git
   cd sepehr-run-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run app.py
   ```

4. **Access the dashboard**
   Open your browser and navigate to `http://localhost:8501`

## 📱 Mobile Optimization

RunTracker features a **mobile-first responsive design** that adapts seamlessly across all devices:

- **Mobile (< 768px)**: Compact summary cards with essential metrics
- **Desktop (≥ 768px)**: Full metric cards with enhanced hover effects
- **Touch-friendly**: 44px minimum touch targets for mobile accessibility
- **Optimized fonts**: Readable typography across all screen sizes

## 🛠️ Technology Stack

- **🤖 AI Engine**: OpenAI GPT for intelligent training plans and analysis
- **Frontend**: Streamlit with custom CSS/HTML
- **Data Processing**: Pandas, NumPy for data manipulation
- **Visualizations**: Plotly for interactive charts
- **Authentication**: Session-based user management
- **Data Storage**: GitHub Gist API for data persistence

## 📊 Data Sources

RunTracker currently supports:
- **Google Sheets** integration for data import
- **GitHub Gist** for data storage and persistence
- **Manual entry** through the web interface
- **CSV data** processing capabilities

## 🎨 Design Philosophy

### Dark Theme with Glass Morphism
- **Background**: Gradient from `#0f172a` to `#334155`
- **Cards**: Glass-morphism with backdrop blur effects
- **Contrast**: WCAG AA compliant (17.06:1 ratio)
- **Animations**: Smooth transitions and hover effects

### Mobile-First Approach
- Progressive enhancement from mobile to desktop
- Responsive breakpoints: 30rem, 48rem, 64rem, 80rem
- Optimized for touch interactions
- Efficient space utilization on small screens

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_SHEETS_CREDENTIALS=path_to_credentials.json
```

### Streamlit Configuration
The app includes optimized Streamlit settings for performance and user experience.

## 📈 Performance Metrics

### Key Performance Indicators
- **Load Time**: < 2 seconds for dashboard rendering
- **Mobile Score**: 100% responsive design compliance
- **Accessibility**: WCAG AA compliant contrast ratios
- **Touch Targets**: 44px minimum for mobile usability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Strava API** for running data integration
- **OpenStreetMap** for route visualization
- **Plotly** for interactive charting capabilities
- **Streamlit** for the amazing web framework

## 📞 Support

For support, email support@runtracker.com or create an issue in this repository.

---

**Built with ❤️ for runners, by runners** 🏃‍♂️💨 