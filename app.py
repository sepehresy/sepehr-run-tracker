import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="Running Dashboard", layout="wide")
st.title("🏃 Summary Statistics")

# Load data
# Use a placeholder for the secret if running locally without secrets configured
try:
    sheet_url = st.secrets["gsheet_url"]
except FileNotFoundError:
    # Provide a dummy URL or path for local testing if secrets aren't available
    st.warning("Streamlit secrets not found. Using placeholder data URL.")
    # Replace with a valid public CSV URL or local path for testing
    sheet_url = "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv" # Example placeholder

@st.cache_data(ttl=3600)
def load_data(url):
    try:
        df = pd.read_csv(url)
        # --- Data Cleaning/Preprocessing specific to your running data ---
        # Ensure 'Date' and 'Distance (km)' columns exist and have correct types
        if 'Date' not in df.columns or 'Distance (km)' not in df.columns:
             st.error(f"Required columns ('Date', 'Distance (km)') not found in the data source: {url}")
             # Return an empty DataFrame with expected columns to prevent further errors
             return pd.DataFrame({'Date': pd.Series(dtype='datetime64[ns]'), 'Distance (km)': pd.Series(dtype='float64')})

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # Attempt to convert distance, coerce errors to NaN, then fill NaN with 0
        df['Distance (km)'] = pd.to_numeric(df['Distance (km)'], errors='coerce').fillna(0)
        df = df.dropna(subset=['Date']) # Remove rows where date conversion failed
        st.success("Data loaded successfully!") # Add success message
        return df
    except Exception as e:
        st.error(f"Failed to load or process data from {url}. Error: {e}")
        # Return an empty DataFrame with expected columns
        return pd.DataFrame({'Date': pd.Series(dtype='datetime64[ns]'), 'Distance (km)': pd.Series(dtype='float64')})


df = load_data(sheet_url)
today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)

# Check if DataFrame is empty after loading
if df.empty:
    st.error("No valid data to display. Please check the data source or column names.")
    st.stop() # Stop execution if no data

# View toggle
view = st.radio(
    "Select View",
    ["Weekly", "4 Weeks", "3 Months", "6 Months", "1 Year", "All (monthly)", "All Yearly"],
    horizontal=True
)

# Chart style toggle
chart_style = st.selectbox(
    "Chart Style",
    ["Bar", "Bar + Line", "Line + Dots", "Area + Dots"],
    index=0
)

# --- Initialize variables used in multiple branches ---
df_agg = pd.DataFrame()
x_encoding = None # Use a dedicated variable for the X encoding object
y_encoding = alt.Y("Distance (km):Q", title="Distance (km)") # Consistent Y encoding
tooltip_fields = []
bar_width_config = {} # Use dict for bar width/size


# --- View-specific processing ---
if view == "Weekly":
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=6)
    df_filtered = df[df["Date"].between(start, end)].copy() # Filter first
    df_filtered["Day"] = df_filtered["Date"].dt.strftime("%a")
    daily_km = df_filtered.groupby("Day")["Distance (km)"].sum()
    # Ensure all days are present and in order
    all_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    df_agg = pd.DataFrame({"Day": all_days})
    df_agg["Distance (km)"] = df_agg["Day"].map(daily_km).fillna(0)

    x_encoding = alt.X("Day:N", title="Day", sort=all_days) # Nominal, sorted correctly
    tooltip_fields = ["Day", "Distance (km)"]
    bar_width_config = {'size': 60}

elif view == "4 Weeks":
    current_week_start = today - timedelta(days=today.weekday())
    start = current_week_start - timedelta(weeks=3) # Start of the first week (4 weeks ago)
    end = current_week_start + timedelta(weeks=1) - timedelta(days=1) # End of the current week
    
    # Create a complete range of weeks
    week_range = pd.date_range(start=start, end=end, freq="W-MON")
    df_agg_base = pd.DataFrame({"Week": week_range})

    # Filter data for the relevant period
    df_filtered = df[df["Date"].between(start, end)].copy()
    if not df_filtered.empty:
        df_filtered["Week"] = df_filtered["Date"].dt.to_period("W-MON").apply(lambda r: r.start_time)
        weekly_km = df_filtered.groupby("Week")["Distance (km)"].sum().reset_index()
        # Merge with the complete week range
        df_agg = pd.merge(df_agg_base, weekly_km, on="Week", how="left").fillna(0)
    else:
        df_agg = df_agg_base
        df_agg["Distance (km)"] = 0

    # Format week label for better readability
    df_agg['Week Label'] = df_agg['Week'].dt.strftime("W %U (%b %d)")

    x_encoding = alt.X("Week Label:N", title="Week", sort=df_agg['Week Label'].tolist()) # Use label for axis
    tooltip_fields = [alt.Tooltip("Week:T", title="Week Start"), "Distance (km)"]
    bar_width_config = {'size': 40}


elif view == "3 Months":
    start = today - relativedelta(months=3)
    start = start.replace(day=1) # Start from beginning of the month
    end = today
    # Create a complete range of weeks
    week_range = pd.date_range(start=start, end=end, freq="W-MON")
    df_agg_base = pd.DataFrame({"Week": week_range})

    # Filter data
    df_filtered = df[df["Date"].between(start, end)].copy()
    if not df_filtered.empty:
        df_filtered["Week"] = df_filtered["Date"].dt.to_period("W-MON").apply(lambda r: r.start_time)
        weekly_km = df_filtered.groupby("Week")["Distance (km)"].sum().reset_index()
        # Merge
        df_agg = pd.merge(df_agg_base, weekly_km, on="Week", how="left").fillna(0)
    else:
        df_agg = df_agg_base
        df_agg["Distance (km)"] = 0

    x_encoding = alt.X("Week:T", title="Week")
    tooltip_fields = [alt.Tooltip("Week:T", title="Week Start"), "Distance (km)"]
    bar_width_config = {'width': alt.Step(10)} # Use step for dynamic width

elif view == "6 Months":
    start = today - relativedelta(months=6)
    start = start.replace(day=1)
    end = today
    week_range = pd.date_range(start=start, end=end, freq="W-MON")
    df_agg_base = pd.DataFrame({"Week": week_range})

    df_filtered = df[df["Date"].between(start, end)].copy()
    if not df_filtered.empty:
        df_filtered["Week"] = df_filtered["Date"].dt.to_period("W-MON").apply(lambda r: r.start_time)
        weekly_km = df_filtered.groupby("Week")["Distance (km)"].sum().reset_index()
        df_agg = pd.merge(df_agg_base, weekly_km, on="Week", how="left").fillna(0)
    else:
        df_agg = df_agg_base
        df_agg["Distance (km)"] = 0

    x_encoding = alt.X("Week:T", title="Week")
    tooltip_fields = [alt.Tooltip("Week:T", title="Week Start"), "Distance (km)"]
    bar_width_config = {'width': alt.Step(8)} # Use step

elif view == "1 Year":
    start = today - relativedelta(years=1)
    start = start.replace(day=1)
    end = today
    # Create a complete range of months
    month_range = pd.date_range(start=start, end=end, freq='MS') # MS for Month Start
    df_agg_base = pd.DataFrame({"Month": month_range})

    # Filter data
    df_filtered = df[df["Date"].between(start, end)].copy()
    if not df_filtered.empty:
        df_filtered["Month"] = df_filtered["Date"].dt.to_period("M").apply(lambda r: r.start_time)
        monthly_km = df_filtered.groupby("Month")["Distance (km)"].sum().reset_index()
        # Merge
        df_agg = pd.merge(df_agg_base, monthly_km, on="Month", how="left").fillna(0)
    else:
        df_agg = df_agg_base
        df_agg["Distance (km)"] = 0

    df_agg["Month Label"] = df_agg["Month"].dt.strftime("%b %Y")
    
    x_encoding = alt.X("Month Label:N", title="Month", sort=df_agg['Month Label'].tolist()) # Sort based on label order
    tooltip_fields = [alt.Tooltip("Month:T", title="Month Start", format="%B %Y"), "Distance (km)"]
    bar_width_config = {'size': 20}


elif view == "All (monthly)":
    if not df.empty:
        df_copy = df.copy() # Work on a copy
        df_copy["MonthStart"] = df_copy["Date"].dt.to_period("M").apply(lambda r: r.start_time)
        monthly_km = df_copy.groupby("MonthStart")["Distance (km)"].sum().reset_index()

        # Ensure all months from min to max date are present
        if not monthly_km.empty:
             min_month = df['Date'].min().to_period("M").start_time
             max_month = df['Date'].max().to_period("M").start_time
             all_months = pd.date_range(start=min_month, end=max_month, freq='MS')
             df_all_months = pd.DataFrame({"MonthStart": all_months})
             df_agg = pd.merge(df_all_months, monthly_km, on="MonthStart", how="left").fillna(0)
        else:
             df_agg = pd.DataFrame({"MonthStart": [], "Distance (km)": []}) # Empty case

        # Add hierarchical fields
        if not df_agg.empty:
             df_agg["Year"] = df_agg["MonthStart"].dt.year
             df_agg["Quarter"] = "Q" + df_agg["MonthStart"].dt.quarter.astype(str)
             df_agg["MonthName"] = df_agg["MonthStart"].dt.strftime("%b")
             # Ensure correct chronological sort before encoding
             df_agg = df_agg.sort_values("MonthStart")
        else: # Handle empty df_agg case after merge
             df_agg["Year"] = pd.Series(dtype='int')
             df_agg["Quarter"] = pd.Series(dtype='str')
             df_agg["MonthName"] = pd.Series(dtype='str')


        # *** MODIFIED X ENCODING FOR HIERARCHICAL AXIS ***
        x_encoding = alt.X(
            'MonthName:O',  # Innermost level: Month abbreviation, Ordinal
            axis=alt.Axis(title=None, labelAngle=-45, grid=False), # Axis for Month, no title
            sort=df_agg['MonthStart'].tolist(), # Ensure month sort order is chronological
             header=alt.Header(
                 titleOrient="top", labelOrient="top", # Titles/Labels above chart
                 titlePadding=-5, # Adjust padding if needed
                 labelPadding=-5, # Adjust padding if needed
                 labelExpr="datum.label == 'Q1' ? datum.label + ' ' + timeFormat(datum.value, '%Y') : datum.label" # Hack to show Year only for Q1 label
             )
        )

        # Use 'header' for Quarter and Year levels. This requires a different structure.
        # Let's define the axis using the multi-field approach directly in X
        x_encoding = alt.X(
            ['Year:O', 'Quarter:O', 'MonthName:O'], # List fields for hierarchy
            axis=alt.Axis(
                title="Year / Quarter / Month",
                labelAngle=-45, # Angle for the innermost label (MonthName)
                grid=False, # Turn off grid lines on x-axis if desired
                labelOverlap=True # Allow labels to overlap if needed, or use False/greedy
            )
            # No separate 'header' needed here
        )
        tooltip_fields = ["Year:O", "Quarter:O", "MonthName:O", "Distance (km)"]
        bar_width_config = {'width': alt.Step(10)} # Use step for dynamic width

    else: # Handle case where initial df is empty
        df_agg = pd.DataFrame({
             "MonthStart": [], "Distance (km)": [], "Year": [], "Quarter": [], "MonthName": []
        })
        x_encoding = alt.X('MonthName:O') # Placeholder
        tooltip_fields = ["Year:O", "Quarter:O", "MonthName:O", "Distance (km)"]
        bar_width_config = {'width': alt.Step(10)}


elif view == "All Yearly":
    if not df.empty:
        df_copy = df.copy()
        df_copy["Year"] = df_copy["Date"].dt.to_period("Y").apply(lambda r: r.start_time)
        yearly_km = df_copy.groupby("Year")["Distance (km)"].sum().reset_index()
        
        # Ensure all years from min to max date are present
        if not yearly_km.empty:
            min_year = df['Date'].min().to_period("Y").start_time
            max_year = df['Date'].max().to_period("Y").start_time
            all_years = pd.date_range(start=min_year, end=max_year, freq='AS') # AS for Year Start
            df_all_years = pd.DataFrame({"Year": all_years})
            df_agg = pd.merge(df_all_years, yearly_km, on="Year", how="left").fillna(0)
            df_agg["YearLabel"] = df_agg["Year"].dt.strftime("%Y") # Use label for axis if needed
        else:
            df_agg = pd.DataFrame({"Year": [], "Distance (km)": [], "YearLabel": []})
    else:
        df_agg = pd.DataFrame({"Year": [], "Distance (km)": [], "YearLabel": []})


    # Display year as a temporal axis or ordinal/nominal based on preference
    # Using Temporal for potentially better spacing if years are skipped
    x_encoding = alt.X("Year:T", title="Year", axis=alt.Axis(format="%Y"))
    # Or use Ordinal for discrete categories:
    # x_encoding = alt.X("YearLabel:O", title="Year")
    
    tooltip_fields = [alt.Tooltip("Year:T", title="Year", format="%Y"), "Distance (km)"]
    bar_width_config = {'size': 30}

# --- Check if df_agg is valid before creating chart ---
if x_encoding is None or df_agg.empty:
    st.warning(f"No data available for the selected view: '{view}'.")
else:
    # --- Base chart ---
    # Use the prepared encodings
    base = alt.Chart(df_agg).encode(
        x=x_encoding,
        y=y_encoding,
        tooltip=tooltip_fields
    )

    # --- Choose chart style ---
    chart = alt.LayerChart() # Initialize LayerChart for combining marks
    if chart_style == "Bar":
        chart += base.mark_bar(**bar_width_config)
    elif chart_style == "Bar + Line":
        chart += base.mark_bar(**bar_width_config)
        chart += base.mark_line(strokeWidth=2, color="orange", point=False) # Ensure points are off for the line if desired
    elif chart_style == "Line + Dots":
        chart += base.mark_line(strokeWidth=2) + base.mark_point(filled=True, size=70)
    elif chart_style == "Area + Dots":
        chart += base.mark_area(opacity=0.5, interpolate="monotone") + base.mark_point(filled=True, size=70)
    
    # Final chart properties
    final_chart = chart.properties(height=400).interactive() # Add interactivity

    st.altair_chart(final_chart, use_container_width=True)
