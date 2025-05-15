import requests
import streamlit as st

def fetch_elevations(coords):
    """
    Given a list of (lat, lon) tuples, return a list of elevations (meters) using Open-Elevation API.
    Returns a list of elevations in the same order as coords.
    """
    if not coords:
        return []
    # Open-Elevation API allows up to 100 points per request
    url = "https://api.open-elevation.com/api/v1/lookup"
    locations = [{"latitude": lat, "longitude": lon} for lat, lon in coords]
    try:
        response = requests.post(url, json={"locations": locations}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [result["elevation"] for result in data["results"]]
        else:
            st.warning(f"Open-Elevation API error: {response.status_code}")
            return [0] * len(coords)
    except Exception as e:
        st.warning(f"Error fetching elevation data: {e}")
        return [0] * len(coords)
