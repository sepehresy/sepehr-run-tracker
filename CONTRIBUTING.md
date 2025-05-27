# Contributing to RunTracker 🏃‍♂️

Thank you for your interest in contributing to RunTracker! We welcome contributions from the running and developer community.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Git
- Basic knowledge of Streamlit and data visualization

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/sepehresy/sepehr-run-tracker.git
   cd sepehr-run-tracker
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🎯 How to Contribute

### 🐛 Bug Reports
- Use the GitHub issue tracker
- Include detailed steps to reproduce
- Provide screenshots if applicable
- Mention your OS and Python version

### ✨ Feature Requests
- Check existing issues first
- Describe the feature and its benefits
- Include mockups or examples if possible

### 🔧 Code Contributions

#### Branch Naming Convention
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

#### Coding Standards
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and small

#### Mobile-First Development
- Always test on mobile devices (320px width minimum)
- Ensure touch targets are at least 44px
- Maintain WCAG AA contrast ratios (4.5:1 minimum)
- Use responsive breakpoints: 30rem, 48rem, 64rem, 80rem

#### CSS Guidelines
- Use the existing design system
- Maintain glass-morphism aesthetic
- Ensure dark theme compatibility
- Test hover states and animations

### 📱 Testing Requirements

#### Desktop Testing
- Chrome, Firefox, Safari, Edge
- Resolutions: 1920x1080, 1366x768, 1280x720

#### Mobile Testing
- iOS Safari, Chrome Mobile, Firefox Mobile
- Screen sizes: 320px, 375px, 414px, 768px

#### Accessibility Testing
- Screen reader compatibility
- Keyboard navigation
- Color contrast validation
- Touch target size verification

## 📝 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make your changes**
   - Write clean, documented code
   - Follow the coding standards
   - Test thoroughly on mobile and desktop

3. **Test your changes**
   ```bash
   # Run the app and test all features
   streamlit run app.py
   
   # Test mobile responsiveness
   # Use browser dev tools to simulate mobile devices
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature
   
   - Detailed description of changes
   - Mobile optimization included
   - Tested on multiple devices"
   ```

5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

6. **Create a Pull Request**
   - Use the PR template
   - Include screenshots of changes
   - Describe testing performed
   - Reference any related issues

## 🎨 Design Guidelines

### Color Palette
- **Background**: Gradient from `#0f172a` to `#334155`
- **Cards**: Glass-morphism with `rgba(255, 255, 255, 0.05)`
- **Text**: High contrast whites and grays
- **Accents**: Blue (`#3b82f6`) for interactive elements

### Typography
- **Headers**: Bold, clear hierarchy
- **Body**: Readable font sizes (minimum 14px)
- **Mobile**: Optimized sizes (minimum 10px for compact layouts)

### Spacing
- **Mobile**: Compact spacing for efficiency
- **Desktop**: Generous spacing for comfort
- **Touch targets**: Minimum 44px for mobile

## 🏃‍♂️ Current Feature Areas

### Core Modules
- **Statistics Dashboard** - Performance metrics and trend analysis
- **Pace Calculator** - Ultra-compact pace and time calculations
- **Activities View** - Workout data management and visualization
- **Fatigue Analysis** - Training load and recovery metrics
- **Race Planning** - AI-powered training plan generation
- **Runner Profile** - User profile and preferences management

### Technical Components
- **Data Processing** - Time/pace parsing and workout type detection
- **Mobile Optimization** - Responsive design and touch interfaces
- **Authentication** - User login and session management
- **Data Storage** - GitHub Gist integration for persistence

## 📊 Code Review Criteria

### Functionality
- ✅ Feature works as intended
- ✅ No breaking changes
- ✅ Error handling implemented
- ✅ Edge cases considered

### Design
- ✅ Mobile-responsive design
- ✅ Consistent with existing UI
- ✅ Accessibility compliant
- ✅ Performance optimized

### Code Quality
- ✅ Clean, readable code
- ✅ Proper documentation
- ✅ Following conventions
- ✅ No code duplication

## 🤝 Community Guidelines

- **Be respectful** and inclusive
- **Help others** learn and grow
- **Share knowledge** and best practices
- **Focus on constructive** feedback
- **Celebrate achievements** together

## 📞 Getting Help

- **GitHub Discussions** for general questions
- **GitHub Issues** for bugs and features
- **Code reviews** for technical guidance
- **Documentation** for setup and usage

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- CHANGELOG.md for significant contributions
- GitHub contributors page
- Special mentions in releases

---

**Happy coding and happy running!** 🏃‍♂️💨

*Remember: Every contribution, no matter how small, makes RunTracker better for the entire running community.* 