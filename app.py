# 📅 --- RACE TRAINING PLAN SECTION ---

import numpy as np

st.header("🏁 Race Training Plan")

# 1. Generate all weeks from first run to race day
start_week = df['Date'].min().to_period("W").start_time
end_week = datetime(2025, 5, 24)
weeks = pd.date_range(start=start_week, end=end_week, freq="W-MON")

# 2. Actual weekly km
df['Week'] = df['Date'].dt.to_period('W').apply(lambda r: r.start_time)
actual_km = df.groupby('Week')['Distance (km)'].sum().reindex(weeks, fill_value=0).reset_index()
actual_km.columns = ['Week', 'Actual']

# 3. Load or create editable plan
if 'plan_df' not in st.session_state:
    st.session_state.plan_df = pd.DataFrame({
        'Week': weeks,
        'Planned': [np.nan] * len(weeks)  # Empty cells for user to edit
    })

plan_df = st.session_state.plan_df.copy()

# 4. Merge plan and actual
merged = pd.merge(plan_df, actual_km, on='Week', how='left')
merged['Planned'] = merged['Planned'].fillna(0)
merged['Delta'] = merged['Actual'] - merged['Planned']
merged['Status'] = np.where(merged['Week'] < datetime.today(), "✅ Done", "⏳ Upcoming")

# 5. Editable table
st.subheader("📋 Weekly Plan (editable)")
edited = st.data_editor(
    merged[['Week', 'Planned']],
    num_rows="dynamic",
    use_container_width=True,
    key="training_plan"
)
# Save edits
st.session_state.plan_df['Planned'] = edited['Planned']

# 6. Plot planned vs actual
st.subheader("📊 Planned vs Actual Distance per Week")
melted = pd.melt(merged, id_vars=["Week"], value_vars=["Planned", "Actual"], var_name="Type", value_name="KM")

highlight = alt.Chart(pd.DataFrame({"x": [pd.to_datetime("2025-05-24")]})).mark_rule(color="red").encode(x='x:T')

chart = alt.Chart(melted).mark_bar().encode(
    x='Week:T',
    y='KM:Q',
    color='Type:N',
    tooltip=['Week', 'Type', 'KM']
).properties(height=400)

# Annotate done weeks
done_points = merged[merged['Week'] < datetime.today()]
done_text = alt.Chart(done_points).mark_text(
    align='center', dy=-10, fontSize=10
).encode(
    x='Week:T',
    y='Actual:Q',
    text='Delta:Q'
)

st.altair_chart((chart + done_text + highlight), use_container_width=True)
