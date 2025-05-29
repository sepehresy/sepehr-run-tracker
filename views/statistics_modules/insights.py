"""
Insights and recommendations generator for running statistics
"""
import pandas as pd


def generate_insights(df_filtered, time_period):
    """Generate personalized insights and recommendations based on running data"""
    insights = []
    
    if len(df_filtered) < 5:
        return insights
    
    # Pace consistency analysis
    if not df_filtered['pace_minutes'].dropna().empty:
        pace_std = df_filtered['pace_minutes'].std()
        pace_mean = df_filtered['pace_minutes'].mean()
        cv = (pace_std / pace_mean) * 100 if pace_mean > 0 else 0
        
        if cv < 10:
            insights.append("🎯 **Excellent pace consistency** - Your pacing is very steady across runs, indicating good race control and training discipline.")
        elif cv < 20:
            insights.append("👍 **Good pace consistency** - Minor variations in pacing are normal and show you're adapting effort to different workout types.")
        else:
            insights.append("⚠️ **Variable pacing** - Consider focusing on consistent effort levels and using a GPS watch or app for better pace feedback.")
    
    # Volume analysis with specific recommendations
    total_distance = df_filtered['Distance (km)'].sum()
    total_runs = len(df_filtered)
    
    if time_period == 7:
        weekly_distance = total_distance
        if weekly_distance < 15:
            insights.append("📈 **Low weekly volume** - Consider gradually increasing by 10% each week. Start with an extra easy run.")
        elif weekly_distance > 80:
            insights.append("⚡ **High weekly volume** - Excellent mileage! Monitor recovery and consider deload weeks every 4th week.")
        elif weekly_distance > 50:
            insights.append("🏃‍♂️ **Strong weekly volume** - Great consistency! Consider adding quality workouts like tempo runs or intervals.")
        else:
            insights.append("✅ **Healthy weekly volume** - Good foundation. Perfect range for steady improvement and injury prevention.")
    
    # Distance progression analysis
    if len(df_filtered) >= 5:
        recent_distances = df_filtered.tail(5)['Distance (km)'].mean()
        earlier_distances = df_filtered.head(5)['Distance (km)'].mean()
        progression = ((recent_distances - earlier_distances) / earlier_distances * 100) if earlier_distances > 0 else 0
        
        if progression > 15:
            insights.append("📊 **Strong distance progression** - Your average run distance has increased significantly. Great for building endurance!")
        elif progression > 5:
            insights.append("📈 **Positive distance trend** - Gradual increase in run length shows smart progression and reduced injury risk.")
        elif progression < -15:
            insights.append("📉 **Decreasing distance trend** - Consider if this aligns with your goals. Recovery phases are normal in training cycles.")
        else:
            insights.append("🔄 **Stable distance pattern** - Consistent run lengths are great for building aerobic base and establishing routine.")
    
    # Heart rate analysis with training zones
    if not df_filtered['Avg HR'].dropna().empty:
        avg_hr_value = df_filtered['Avg HR'].mean()
        if avg_hr_value > 170:
            insights.append("🔥 **High intensity focus** - Most runs are at high intensity. Consider adding easy aerobic runs for better recovery.")
        elif avg_hr_value > 150:
            insights.append("⚡ **Moderate-high intensity** - Good mix of efforts. Ensure 80% of runs are easy pace for optimal adaptation.")
        elif avg_hr_value < 130:
            insights.append("🟢 **Aerobic base building** - Excellent easy running! Perfect for building endurance foundation and fat adaptation.")
        else:
            insights.append("⚖️ **Balanced intensity distribution** - Great mix of easy and moderate efforts following the 80/20 training principle.")
    
    # Weekly frequency analysis
    if time_period and time_period >= 7:
        runs_per_week = total_runs / (time_period / 7)
        if runs_per_week < 2:
            insights.append("📅 **Low frequency** - Try to run at least 3 times per week for better adaptation and habit formation.")
        elif runs_per_week > 6:
            insights.append("🏃‍♂️ **High frequency runner** - Excellent consistency! Make sure to prioritize sleep and nutrition for recovery.")
        elif runs_per_week >= 4:
            insights.append("✨ **Optimal frequency** - 4-6 runs per week is the sweet spot for most runners to see consistent improvement.")
        else:
            insights.append("👌 **Good frequency** - 3-4 runs per week provides solid fitness gains while allowing adequate recovery.")
    
    # Performance trend analysis
    if len(df_filtered) >= 10:
        pace_data = df_filtered.dropna(subset=['pace_minutes']).sort_values('Date')
        if len(pace_data) >= 10:
            recent_pace = pace_data.tail(5)['pace_minutes'].mean()
            earlier_pace = pace_data.head(5)['pace_minutes'].mean()
            pace_improvement = ((earlier_pace - recent_pace) / earlier_pace * 100) if earlier_pace > 0 else 0
            
            if pace_improvement > 5:
                insights.append("🚀 **Improving pace** - Your speed has increased significantly! Your training is paying off.")
            elif pace_improvement > 2:
                insights.append("📈 **Gradual pace improvement** - Steady progress is sustainable progress. Keep up the consistent training!")
            elif pace_improvement < -5:
                insights.append("🔄 **Pace variation** - Consider if recent runs included more hills, weather challenges, or recovery runs.")
    
    # Elevation analysis
    if not df_filtered['Elevation Gain'].dropna().empty:
        total_elevation = df_filtered['Elevation Gain'].sum()
        avg_elevation_per_run = total_elevation / total_runs if total_runs > 0 else 0
        
        if avg_elevation_per_run > 100:
            insights.append("⛰️ **Hill training champion** - Great elevation gain! Hills build strength and improve running economy.")
        elif avg_elevation_per_run > 50:
            insights.append("🏔️ **Moderate hill training** - Good mix of flat and hilly runs. Consider adding more hill repeats for strength.")
        elif avg_elevation_per_run < 10:
            insights.append("🏃‍♀️ **Flat terrain runner** - Consider adding some hill training to improve strength and power.")
    
    # Cadence analysis
    if not df_filtered['Cadence'].dropna().empty:
        cadence_data = pd.to_numeric(df_filtered['Cadence'], errors='coerce').dropna()
        if not cadence_data.empty:
            avg_cadence = cadence_data.mean()
            if avg_cadence > 180:
                insights.append("👟 **Optimal cadence** - Your step rate is in the ideal range for efficient running form.")
            elif avg_cadence > 170:
                insights.append("🦵 **Good cadence** - Slightly increasing your step rate could improve efficiency and reduce injury risk.")
            elif avg_cadence < 160:
                insights.append("⏰ **Low cadence** - Consider working on quicker, shorter steps to improve running efficiency.")
    
    # Training load analysis
    if time_period and time_period >= 14:  # At least 2 weeks of data
        from .data_processing import calculate_training_load_score
        training_load = calculate_training_load_score(df_filtered)
        load_per_week = training_load / (time_period / 7)
        
        if load_per_week > 200:
            insights.append("🔥 **High training load** - Monitor fatigue levels and ensure adequate recovery between hard sessions.")
        elif load_per_week > 100:
            insights.append("💪 **Moderate training load** - Good balance of volume and intensity. Perfect for steady improvement.")
        elif load_per_week < 50:
            insights.append("📊 **Conservative training load** - Room to gradually increase either volume or intensity for faster progress.")
    
    # Workout type diversity analysis
    if 'Name' in df_filtered.columns or 'Activity Name' in df_filtered.columns:
        from .data_processing import detect_workout_type
        df_with_types = df_filtered.copy()
        df_with_types['workout_type'] = df_with_types.apply(detect_workout_type, axis=1)
        workout_types = df_with_types['workout_type'].value_counts()
        
        if len(workout_types) == 1 and workout_types.index[0] == 'Default':
            insights.append("🎯 **Training variety opportunity** - Consider adding different workout types like tempo runs, intervals, or long runs.")
        elif 'Race' in workout_types.index:
            race_count = workout_types['Race']
            if race_count >= 2:
                insights.append("🏆 **Active racer** - Great job participating in races! They're excellent for motivation and performance testing.")
        
        if 'Long Run' in workout_types.index:
            long_run_percentage = (workout_types['Long Run'] / total_runs) * 100
            if long_run_percentage > 30:
                insights.append("🏃‍♂️ **Long run focused** - Excellent endurance building! Make sure to include some speed work for balanced training.")
            elif long_run_percentage < 10:
                insights.append("📏 **Add long runs** - Include one longer run per week to build endurance and mental toughness.")
    
    return insights


def get_no_insights_message():
    """Return message when there's insufficient data for insights"""
    return """
    <div style="text-align: center; padding: 3rem 2rem; color: #6b7280; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 16px; border: 1px solid #e2e8f0;">
        <h3 style="color: #4b5563; margin-bottom: 1rem;">🏃‍♂️ Ready for Insights!</h3>
        <p style="font-size: 1.1rem; margin-bottom: 0;">Keep logging your runs to unlock personalized insights and training recommendations!</p>
        <p style="font-size: 0.9rem; opacity: 0.8;">We need at least 5 runs to provide meaningful analysis.</p>
    </div>
    """ 