"""
CSS styles for the race planning module.
"""

import streamlit as st

def load_app_css():
    """Load all CSS for the race planning app."""
    st.markdown("""
    <style>
    /* Modern UI Styles for Race Planning */
    
    /* Base Styles */
    div[data-baseweb="select"] > div {
        min-height: 40px !important;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.3rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(49, 51, 63, 0.2);
        display: flex;
        align-items: center;
    }
    
    /* Dividers */
    .modern-hr {
        margin: 1.5rem 0;
        border: none;
        height: 1px;
        background-color: rgba(49, 51, 63, 0.2);
    }
    
    /* Card Styles */
    .card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #dee2e6;
        transition: all 0.2s;
    }
    
    .card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* Race Card Styles */
    .race-card {
        display: flex;
        flex-direction: column;
        cursor: pointer;
    }
    
    .race-card-header {
        display: flex;
        justify-content: space-between;
        align-items: start;
    }
    
    .race-card-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0;
    }
    
    .race-card-subtitle {
        color: #6c757d;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    
    .race-card-badge {
        background-color: #28a745;
        color: white;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .race-card-progress {
        background-color: #e9ecef;
        height: 6px;
        border-radius: 3px;
        margin-top: 12px;
        margin-bottom: 5px;
        overflow: hidden;
    }
    
    .race-card-progress-bar {
        height: 100%;
        background-color: #28a745;
        transition: width 0.3s;
    }
    
    .race-card-footer {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        color: #6c757d;
    }
    
    /* Week Card Styles */
    .week-card {
        display: flex;
        align-items: center;
        padding: 12px 15px;
        border-radius: 8px;
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .week-card:hover {
        background-color: #f8f9fa;
    }
    
    .week-current {
        background-color: #e8f4f8;
        border: 2px solid #1EBEFF;
    }
    
    .week-race {
        background-color: #fff9e6;
        border: 2px solid #FFD700;
    }
    
    .week-icon {
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        background-color: #6c757d;
        color: white;
        font-weight: bold;
        margin-right: 12px;
        flex-shrink: 0;
    }
    
    .week-info {
        flex-grow: 1;
    }
    
    .week-title {
        font-weight: 500;
    }
    
    .week-dates {
        font-size: 0.85rem;
        color: #6c757d;
    }
    
    .week-chart {
        display: flex;
        height: 40px;
        align-items: flex-end;
        margin-right: 15px;
    }
    
    .week-chart-bar {
        width: 6px;
        background-color: #4CAF50;
        border-radius: 2px;
        margin-right: 3px;
    }
    
    .week-total {
        font-weight: bold;
        min-width: 60px;
        text-align: right;
    }
    
    /* Day Card Styles */
    .day-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        position: relative;
        height: 170px;
        transition: all 0.2s;
        cursor: pointer;
    }
    
    .day-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .day-card-race {
        background-color: #fff9e6;
        border: 2px solid #FFD700;
    }
    
    .day-card-workout {
        background-color: #e8f4f8;
        border: 1px solid #1EBEFF;
    }
    
    .day-card-rest {
        background-color: #f8f9fa;
    }
    
    .day-title {
        font-weight: 500;
    }
    
    .day-date {
        font-size: 0.85rem;
        color: #6c757d;
        margin-bottom: 10px;
    }
    
    .day-distance {
        font-size: 1.4rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    .day-description {
        font-size: 0.9rem;
        color: #212529;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
    }
    
    .day-icon {
        position: absolute;
        top: 10px;
        right: 10px;
        font-size: 1.3rem;
    }
    
    /* Button Styles */
    .primary-button {
        background-color: #007bff;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .primary-button:hover {
        background-color: #0069d9;
    }
    
    .secondary-button {
        background-color: #6c757d;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 500;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .secondary-button:hover {
        background-color: #5a6268;
    }
    
    /* Analysis Panel Styles */
    .analysis-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    }
    
    .analysis-date {
        font-size: 0.9rem;
        color: #6c757d;
        margin-bottom: 10px;
    }
    
    /* Coach Notes */
    .coach-notes {
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 10px 15px;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    
    .coach-notes-title {
        font-weight: 500;
        margin-bottom: 5px;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        color: white;
    }
    
    .status-completed {
        background-color: #28a745;
    }
    
    .status-in-progress {
        background-color: #007bff;
    }
    
    .status-modified {
        background-color: #fd7e14;
    }
    
    .status-future {
        background-color: #6c757d;
    }
    
    /* Edit Form Styles */
    .edit-form-section {
        margin-bottom: 20px;
    }
    
    .edit-form-label {
        font-weight: 500;
        margin-bottom: 5px;
    }
    
    /* Improve Streamlit Components */
    .stTextInput > div > div {
        border-radius: 6px !important;
    }
    
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 500 !important;
    }
    
    /* Modal Overlay */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.5);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .modal-content {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        width: 80%;
        max-width: 600px;
        max-height: 90vh;
        overflow-y: auto;
    }
    
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .modal-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin: 0;
    }
    
    .modal-close {
        cursor: pointer;
        font-size: 1.5rem;
        line-height: 1;
    }
    </style>
    """, unsafe_allow_html=True) 