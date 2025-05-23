"""
Data handling functions for race planning module.
"""

import streamlit as st
from utils.gist_helpers import load_gist_data, save_gist_data


def load_gist_race_data(user_info, gist_id, filename, token):
    """Load race data from a gist."""
    data = load_gist_data(gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    if user_key not in data:
        data[user_key] = {"races": [], "training_plans": {}, "progress_feedback": {}}
    return data


def save_gist_race_data(data, user_info, gist_id, filename, token):
    """Save race data to a gist."""
    return save_gist_data(gist_id, filename, token, data)


def load_saved_races(user_info, gist_id, filename, token):
    """Load saved races for a user."""
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    return data[user_key].get("races", [])


def save_races(races, user_info, gist_id, filename, token):
    """Save races for a user."""
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    data[user_key]["races"] = races
    return save_gist_race_data(data, user_info, gist_id, filename, token)


def load_training_plans(user_info, gist_id, filename, token):
    """Load training plans for a user."""
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    return data[user_key].get("training_plans", {})


def save_training_plan(race_id, plan, user_info, gist_id, filename, token):
    """Save a training plan for a race."""
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    data[user_key].setdefault("training_plans", {})
    data[user_key]["training_plans"][race_id] = plan
    return save_gist_race_data(data, user_info, gist_id, filename, token)


def load_progress_feedback(user_info, gist_id, filename, token):
    """Load progress feedback for a user."""
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    return data[user_key].get("progress_feedback", {})


def save_progress_feedback(race_id, entry, user_info, gist_id, filename, token):
    """Save progress feedback for a race."""
    data = load_gist_race_data(user_info, gist_id, filename, token)
    user_key = user_info["USER_KEY"]
    data[user_key].setdefault("progress_feedback", {})
    data[user_key]["progress_feedback"].setdefault(race_id, []).append(entry)
    return save_gist_race_data(data, user_info, gist_id, filename, token)


def render_feedback_history(race_id, user_info, gist_id, filename, token):
    """
    Render feedback history for a race.
    
    Args:
        race_id: Race ID
        user_info: User information
        gist_id: Gist ID
        filename: Filename
        token: GitHub token
    """
    race_history = load_progress_feedback(user_info, gist_id, filename, token).get(race_id, [])
    
    if race_history:
        # The feedback history is already rendered in the visualization module
        pass 