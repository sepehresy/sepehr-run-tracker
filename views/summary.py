import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from version import APP_VERSION, APP_VERSION_COLOR, APP_VERSION_STYLE

def render_summary(df, today):
    st.sidebar.markdown(f'<div style="position:fixed;bottom:1.5rem;left:0;width:100%;text-align:left;{APP_VERSION_STYLE}color:{APP_VERSION_COLOR};">v{APP_VERSION}</div>', unsafe_allow_html=True)

    st.markdown('<span style="font-size:1.5rem;vertical-align:middle;">🏃</span> <span style="font-size:1.25rem;font-weight:600;vertical-align:middle;">Summary Statistics</span>', unsafe_allow_html=True)

    view_option = st.radio(
        "Select View",
        ["Weekly", "4 Weeks", "3 Months", "6 Months", "1 Year", "All (monthly)", "All Yearly"],
        index=2,  # Default to '3 Months'
        horizontal=True
    )

    # Modern, minimalistic style for metric/chart selectors
    st.markdown("""
    <style>
    .metric-chart-row {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
        align-items: center;
    }
    .metric-chart-row > div {
        flex: 1 1 0;
        min-width: 220px;
    }
    .stSelectbox label, .stRadio label {
        font-weight: 600 !important;
        color: #1EBEFF !important;
        font-size: 1.08rem !important;
        letter-spacing: 0.01em;
    }
    .stSelectbox, .stRadio {
        background: #18191a !important;
        border-radius: 8px !important;
        padding: 0.5rem 0.7rem !important;
        border: 1px solid #23272f !important;
        margin-bottom: 0 !important;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background: #23272f !important;
        border-radius: 6px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Use columns for a modern horizontal layout
    metric_col_ui, chart_col_ui = st.columns(2)
    with metric_col_ui:
        metric_option = st.selectbox(
            "Select Metric",
            [
                "Distance (km)",
                "Avg Heart Rate",
                "Avg Pace",
                "Avg Cadence",
                "Total Time",
                "Elevation Gain"
            ],
            index=0,
            key="metric_select"
        )
    with chart_col_ui:
        chart_style = st.selectbox(
            "Chart Style",
            ["Bar", "Bar + Line", "Line + Dots", "Area + Dots"],
            index=3,  # Default to Area + Dots
            key="chart_style_select"
        )

    # Helper: get y field and aggregation
    metric_map = {
        "Distance (km)": ("Distance (km)", "sum", "Distance (km)", "Distance (km):Q", "Distance (km)"),
        "Avg Heart Rate": ("Avg HR", "mean", "Avg HR", "Avg HR:Q", "Avg HR"),
        "Avg Pace": ("Pace (min/km)", "mean", "Pace (min/km)", "Pace (min/km):Q", "Pace (min/km)"),
        "Avg Cadence": ("Cadence", "mean", "Cadence", "Cadence:Q", "Cadence"),
        # Fix: Convert Moving Time (seconds) to hours for display
        "Total Time": ("Moving Time", "sum", "Total Time (h)", "Total Time (h):Q", "Total Time (h)"),
        "Elevation Gain": ("Elevation Gain", "sum", "Elevation Gain", "Elevation Gain:Q", "Elevation Gain"),
    }
    metric_col, metric_agg, metric_label, y_field, tooltip_label = metric_map[metric_option]

    # --- STEP 1: Parse Moving Time column (MM:SS:00 format) ---
    def parse_minutes_seconds(val):
        """Parse MM:SS:00 string and return total minutes as float."""
        if pd.isnull(val):
            return 0.0
        parts = str(val).split(":")
        try:
            if len(parts) >= 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes + seconds / 60.0
            elif len(parts) == 1:
                return float(parts[0])
            else:
                return 0.0
        except Exception:
            return 0.0

    if "Moving Time" in df.columns:

        df["Moving Time (min)"] = df["Moving Time"].apply(parse_minutes_seconds)
    else:
        df["Moving Time (min)"] = 0.0

    # --- STEP 2: Aggregate and display total time ---
    if metric_option == "Total Time":
        # Handle all aggregation and chart setup for Total Time here
        if view_option == "Weekly":
            start = today - timedelta(days=6)
            end = today
            df_week = df[(df["Date"] >= start) & (df["Date"] <= end)].copy()
            df_week["Day"] = df_week["Date"].dt.strftime("%a (%b %d)")
            ordered_days = [(start + timedelta(days=i)) for i in range(7)]
            day_labels = [(d.strftime("%a (%b %d)")) for d in ordered_days]
            agg = df_week.groupby("Day")["Moving Time (min)"].sum().reindex(day_labels).fillna(0).reset_index()
            agg["Total Time (min)"] = agg["Moving Time (min)"]
            df_agg = agg
            x_field = "Day:N"
            x_title = "Day"
            bar_width = 60
            x_axis = alt.Axis(title=x_title)
            metric_label = "Total Time (min)"
        elif view_option == "4 Weeks":
            current_week_start = today - timedelta(days=today.weekday())
            start = current_week_start - timedelta(weeks=4)
            weeks = [start + timedelta(weeks=i) for i in range(5)]
            df["Week"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit='d')
            df["Week"] = df["Week"].dt.normalize()
            agg = df.groupby("Week")["Moving Time (min)"].sum().reset_index()
            df_agg = pd.DataFrame({"Week": weeks}).merge(agg, on="Week", how="left").fillna(0)
            df_agg["Total Time (h)"] = df_agg["Moving Time (min)"] / 60.0
            x_field = "WeekLabel:N"
            df_agg["WeekLabel"] = "Week-" + df_agg["Week"].dt.isocalendar().week.astype(str)
            x_title = "Week #"
            bar_width = 40
            x_axis = alt.Axis(title=x_title, labelOverlap=False)
            metric_label = "Total Time (h)"
        elif view_option in ["3 Months", "6 Months"]:
            months_back = 3 if view_option == "3 Months" else 6
            start = today - relativedelta(months=months_back)
            first_week_start = (start - timedelta(days=start.weekday()))
            last_week_start = (today - timedelta(days=today.weekday()))
            num_weeks = ((last_week_start - first_week_start).days // 7) + 1
            all_weeks = [first_week_start + timedelta(weeks=i) for i in range(num_weeks)]
            df["Week"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit='d')
            df["Week"] = df["Week"].dt.normalize()
            agg = df[df["Week"] >= first_week_start].groupby("Week")["Moving Time (min)"].sum().reset_index()
            df_agg = pd.DataFrame({"Week": all_weeks}).merge(agg, on="Week", how="left").fillna(0)
            df_agg["Total Time (h)"] = df_agg["Moving Time (min)"] / 60.0
            df_agg = df_agg.sort_values("Week")
            df_agg["WeekLabel"] = "Week-" + df_agg["Week"].dt.isocalendar().week.astype(str)
            x_field = "WeekLabel:N"
            x_title = "Week #"
            bar_width = 20
            x_axis = alt.Axis(title=x_title, labelAngle=-45, labelFontSize=10)
            metric_label = "Total Time (h)"
        elif view_option == "1 Year":
            months = [(today.replace(day=1) - relativedelta(months=12 - i)) for i in range(13)]
            df["Month"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
            agg = df.groupby("Month")["Moving Time (min)"].sum().reset_index()
            df_months = pd.DataFrame({"Month": months}).merge(agg, on="Month", how="left").fillna(0)
            df_months["Month Label"] = df_months["Month"].dt.strftime("%b %Y")
            df_months["Total Time (h)"] = df_months["Moving Time (min)"] / 60.0
            df_agg = df_months
            x_field = "Month Label:N"
            x_title = "Month"
            bar_width = 20
            x_axis = alt.Axis(title=x_title, labelAngle=-45)
            sort_field = "Month"
            metric_label = "Total Time (h)"
        elif view_option == "All (monthly)":
            df["MonthStart"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
            agg = df.groupby("MonthStart")["Moving Time (min)"].sum().reset_index()
            agg["Total Time (h)"] = agg["Moving Time (min)"] / 60.0
            df_agg = agg
            x_field = "MonthStart:T"
            x_title = "Month"
            bar_width = 10
            x_axis = alt.Axis(title=x_title, labelAngle=-45, labelFontSize=10)
            year_lines = alt.Chart(df_agg[df_agg["MonthStart"].dt.month == 1]).mark_rule(
                strokeDash=[4, 4], color="gray"
            ).encode(x="MonthStart:T")
            metric_label = "Total Time (h)"
        elif view_option == "All Yearly":
            df["Year"] = df["Date"].dt.year
            agg = df.groupby("Year")["Moving Time (min)"].sum().reset_index()
            if not agg.empty:
                min_year = agg["Year"].min()
                max_year = agg["Year"].max()
                all_years = list(range(min_year, max_year + 1))
                df_agg = pd.DataFrame({"Year": all_years}).merge(agg, on="Year", how="left").fillna(0)
                df_agg["Total Time (h)"] = df_agg["Moving Time (min)"] / 60.0
            else:
                df_agg = pd.DataFrame(columns=["Year", "Total Time (h)"])
            x_field = "Year:O"
            x_title = "Year"
            bar_width = 40
            x_axis = alt.Axis(title=x_title, labelAngle=0, labelFontSize=12)
            metric_label = "Total Time (h)"
    else:
        # All other metrics: original logic
        if view_option == "Weekly":
            start = today - timedelta(days=6)
            end = today
            df_week = df[(df["Date"] >= start) & (df["Date"] <= end)].copy()
            ordered_days = [(start + timedelta(days=i)) for i in range(7)]
            day_labels = [(d.strftime("%a (%b %d)")) for d in ordered_days]
            df_week["Day"] = df_week["Date"].dt.strftime("%a (%b %d)")
            if metric_agg == "sum":
                df_metrics = df_week.groupby("Day")[[metric_col]].sum().reindex(day_labels).fillna(0).reset_index()
            else:
                df_metrics = df_week.groupby("Day")[[metric_col]].mean().reindex(day_labels).fillna(0).reset_index()
            df_metrics.rename(columns={metric_col: metric_label}, inplace=True)
            if metric_option == "Distance (km)":
                df_metrics["PaceLabel"] = df_week.groupby("Day")["Pace (min/km)"].mean().reindex(day_labels).fillna(0).apply(lambda x: f"Pace={int(x)}:{int((x%1)*60):02d}" if x > 0 else "").values
                df_metrics["HRLabel"] = df_week.groupby("Day")["Avg HR"].mean().reindex(day_labels).fillna(0).apply(lambda x: f"HR={int(x)}" if x > 0 else "").values
                df_metrics["CadLabel"] = df_week.groupby("Day")["Cadence"].mean().reindex(day_labels).fillna(0).apply(lambda x: f"Cad={int(x)}" if x > 0 else "").values
                df_metrics["ElevLabel"] = df_week.groupby("Day")["Elevation Gain"].sum().reindex(day_labels).fillna(0).apply(lambda x: f"Elev={int(x)}" if x > 0 else "").values
            df_agg = df_metrics
            x_field = "Day:N"
            x_title = "Day"
            bar_width = 60
            x_axis = alt.Axis(title=x_title)
        elif view_option == "4 Weeks":
            current_week_start = today - timedelta(days=today.weekday())
            start = current_week_start - timedelta(weeks=4)
            weeks = [start + timedelta(weeks=i) for i in range(5)]
            df["Week"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit='d')
            df["Week"] = df["Week"].dt.normalize()
            if metric_agg == "sum":
                weekly_metric = df.groupby("Week")[[metric_col]].sum().reset_index()
            else:
                weekly_metric = df.groupby("Week")[[metric_col]].mean().reset_index()
            weekly_metric.rename(columns={metric_col: metric_label}, inplace=True)
            df_agg = pd.DataFrame({"Week": weeks}).merge(weekly_metric, on="Week", how="left").fillna(0)
            df_agg["WeekStart"] = df_agg["Week"]
            df_agg["WeekLabel"] = "Week-" + df_agg["WeekStart"].dt.isocalendar().week.astype(str)
            x_field = "WeekLabel:N"
            x_title = "Week #"
            bar_width = 40
            x_axis = alt.Axis(title=x_title, labelOverlap=False)
        elif view_option in ["3 Months", "6 Months"]:
            months_back = 3 if view_option == "3 Months" else 6
            start = today - relativedelta(months=months_back)
            first_week_start = (start - timedelta(days=start.weekday()))
            last_week_start = (today - timedelta(days=today.weekday()))
            num_weeks = ((last_week_start - first_week_start).days // 7) + 1
            all_weeks = [first_week_start + timedelta(weeks=i) for i in range(num_weeks)]
            df["Week"] = df["Date"] - pd.to_timedelta(df["Date"].dt.weekday, unit='d')
            df["Week"] = df["Week"].dt.normalize()
            if metric_agg == "sum":
                weekly_metric = df[df["Week"] >= first_week_start].groupby("Week")[[metric_col]].sum().reset_index()
            else:
                weekly_metric = df[df["Week"] >= first_week_start].groupby("Week")[[metric_col]].mean().reset_index()
            weekly_metric.rename(columns={metric_col: metric_label}, inplace=True)
            df_agg = pd.DataFrame({"Week": all_weeks}).merge(weekly_metric, on="Week", how="left").fillna(0)
            df_agg["WeekStart"] = df_agg["Week"]
            df_agg = df_agg.sort_values("WeekStart")
            df_agg["WeekLabel"] = "Week-" + df_agg["WeekStart"].dt.isocalendar().week.astype(str)
            x_field = "WeekLabel:N"
            x_title = "Week #"
            bar_width = 20
            x_axis = alt.Axis(title=x_title, labelAngle=-45, labelFontSize=10)
        elif view_option == "1 Year":
            months = [(today.replace(day=1) - relativedelta(months=12 - i)) for i in range(13)]
            df["Month"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
            if metric_agg == "sum":
                monthly_metric = df.groupby("Month")[[metric_col]].sum().reset_index()
            else:
                monthly_metric = df.groupby("Month")[[metric_col]].mean().reset_index()
            monthly_metric.rename(columns={metric_col: metric_label}, inplace=True)
            df_months = pd.DataFrame({"Month": months}).merge(monthly_metric, on="Month", how="left").fillna(0)
            df_months["Month Label"] = df_months["Month"].dt.strftime("%b %Y")
            df_agg = df_months
            x_field = "Month Label:N"
            x_title = "Month"
            bar_width = 20
            x_axis = alt.Axis(title=x_title, labelAngle=-45)
            sort_field = "Month"
        elif view_option == "All (monthly)":
            df["MonthStart"] = df["Date"].dt.to_period("M").apply(lambda r: r.start_time)
            if metric_agg == "sum":
                monthly_metric = df.groupby("MonthStart")[[metric_col]].sum(numeric_only=True).reset_index()
            else:
                monthly_metric = df.groupby("MonthStart")[[metric_col]].mean(numeric_only=True).reset_index()
            monthly_metric.rename(columns={metric_col: metric_label}, inplace=True)
            df_agg = monthly_metric
            x_field = "MonthStart:T"
            x_title = "Month"
            bar_width = 10
            x_axis = alt.Axis(title=x_title, labelAngle=-45, labelFontSize=10)
            year_lines = alt.Chart(df_agg[df_agg["MonthStart"].dt.month == 1]).mark_rule(
                strokeDash=[4, 4], color="gray"
            ).encode(x="MonthStart:T")
        elif view_option == "All Yearly":
            df["Year"] = df["Date"].dt.year
            if metric_agg == "sum":
                yearly_metric = df.groupby("Year")[[metric_col]].sum(numeric_only=True).reset_index()
            else:
                yearly_metric = df.groupby("Year")[[metric_col]].mean(numeric_only=True).reset_index()
            yearly_metric.rename(columns={metric_col: metric_label}, inplace=True)
            if not yearly_metric.empty:
                min_year = yearly_metric["Year"].min()
                max_year = yearly_metric["Year"].max()
                all_years = list(range(min_year, max_year + 1))
                df_agg = pd.DataFrame({"Year": all_years}).merge(yearly_metric, on="Year", how="left").fillna(0)
            else:
                df_agg = pd.DataFrame(columns=["Year", metric_label])
            x_field = "Year:O"
            x_title = "Year"
            bar_width = 40
            x_axis = alt.Axis(title=x_title, labelAngle=0, labelFontSize=12)

    # Only override sort_field for "1 Year" view, otherwise keep previous logic
    if 'x_field' in locals() and view_option != "1 Year":
        sort_field = x_field.split(":")[0] if x_field.endswith(":N") else None
    elif view_option == "1 Year":
        # sort_field is set in the 1 Year block above if needed
        pass
    else:
        sort_field = None

    # After df_agg is created, convert Moving Time to hours if needed
    # (No need to divide by 60 again, aggregation already handled above)
    if metric_option == "Total Time" and not df_agg.empty:
        metric_label = "Total Time (h)" if view_option != "Weekly" else "Total Time (min)"

    # Only override sort_field for "1 Year" view, otherwise keep previous logic
    if view_option != "1 Year":
        sort_field = x_field.split(":")[0] if x_field.endswith(":N") else None

    if view_option == "Weekly":
        tooltip_fields = ["Day", metric_label]
        if metric_option == "Distance (km)":
            tooltip_fields += ["PaceLabel", "HRLabel", "CadLabel", "ElevLabel"]
    else:
        tooltip_fields = [df_agg.columns[0], metric_label]

    base = alt.Chart(df_agg).encode(
        x=alt.X(x_field, title=x_title, axis=x_axis, sort=df_agg[sort_field].tolist() if sort_field else None),
        y=alt.Y(f"{metric_label}:Q", title=metric_label),
        tooltip=tooltip_fields
    )

    if chart_style == "Bar":
        chart = base.mark_bar(size=bar_width)
    elif chart_style == "Bar + Line":
        chart = base.mark_bar(size=bar_width) + base.mark_line(strokeWidth=2, color="orange")
    elif chart_style == "Line + Dots":
        chart = base.mark_line(strokeWidth=2) + base.mark_point(filled=True, size=70)
    elif chart_style == "Area + Dots":
        chart = base.mark_area(opacity=0.5, interpolate="linear") + base.mark_point(filled=True, size=70)

    # Add value annotations on top of bars/points
    annotation = alt.Chart(df_agg).mark_text(
        align="center",
        baseline="bottom",
        dy=-8,
        fontSize=13,
        fontWeight="bold",
        color="#1EBEFF" if chart_style in ["Bar", "Bar + Line"] else "#FF9633"
    ).encode(
        x=alt.X(x_field, sort=df_agg[sort_field].tolist() if sort_field else None),
        y=alt.Y(f"{metric_label}:Q"),
        text=alt.Text(f"{metric_label}:Q", format=".1f" if metric_agg == "mean" else ".0f")
    )

    chart += annotation

    if view_option == "All (monthly)":
        chart = chart + year_lines

    if view_option == "Weekly" and metric_option == "Distance (km)":
        for i, label_field in enumerate(["PaceLabel", "HRLabel", "CadLabel", "ElevLabel"]):
            extra_anno = alt.Chart(df_agg).mark_text(
                color="white",
                align="center",
                baseline="bottom",
                dy=-15 * (i + 2),  # move below the value annotation
                fontSize=11
            ).encode(
                x=alt.X(x_field, sort=df_agg["Day"].tolist()),
                y=alt.Y("Distance (km):Q"),
                text=label_field
            )
            chart += extra_anno

    st.altair_chart(chart.properties(height=400), use_container_width=True)
