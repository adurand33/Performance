import streamlit as st
import pandas as pd
import json
import re
import os
import base64
import io
from datetime import datetime
from PIL import Image

# --- Custom CSS for centered header ---
st.markdown("""
<style>
    .header-container {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        margin-bottom: 30px;
    }
    .header-title {
        color: #FFF53F !important;
        margin: 0 !important;
        padding: 0 !important;
        text-align: center;
        text-shadow: 1px 1px 2px #DAA520;
    }
    .header-logo {
        height: 80px !important;
        width: auto !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Utility Functions ---
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

@st.cache_data(ttl=5)
def load_data():
    try:
        with open('athletes.json', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return {}

def time_to_seconds(time_str):
    try:
        clean_str = str(time_str).strip().replace('"', "'")
        if "h" in clean_str:
            h_part, rest = clean_str.split("h", 1)
            m_part, s_part = rest.split("'", 1)
            return int(h_part)*3600 + int(m_part)*60 + float(s_part.replace("'", ""))
        parts = [p for p in re.split(r"['\"]", clean_str) if p]
        if len(parts) == 2:
            return float(parts[0])*60 + float(parts[1])
        elif len(parts) == 3:
            return float(parts[0])*60 + float(parts[1]) + float(parts[2])/100
        return float(clean_str.replace("'", "."))
    except:
        return 0

def event_to_meters(event):
    try:
        event = str(event)
        if match := re.match(r'(\d+)m', event.split()[0]):
            return float(match.group(1))
        road_events = {
            "5km Road": 5001,
            "10km Road": 10001,
            "20km Road": 20001,
            "1/2 Marathon": 21097.5
        }
        return road_events.get(event, 0)
    except:
        return 0

def make_non_interactive_table(df, show_header=False):
    html = ['<table style="width:100%; border-collapse:collapse; margin:0">']
    if show_header:
        html.append('<tr style="background-color:#F0F2F6">')
        for col in df.columns:
            html.append(f'<th style="padding:8px 12px; text-align:left; font-weight:600">{col}</th>')
        html.append('</tr>')
    
    for _, row in df.iterrows():
        html.append('<tr>')
        for col in df.columns:
            html.append(f'<td style="padding:8px 12px; border-bottom:1px solid #E6E6E6">{row[col]}</td>')
        html.append('</tr>')
    
    html.append('</table>')
    return '\n'.join(html)

# --- Main App ---
def main():
    st.set_page_config(layout="wide", page_title="Athlete 🏆 Tracker")
    
    # Display header with logo
    LOGO_PATH = "logo.png"
    if os.path.exists(LOGO_PATH):
        logo = Image.open(LOGO_PATH)
        st.markdown(
            f"""
            <div class="header-container">
                <img src="data:image/png;base64,{image_to_base64(logo)}" class="header-logo">
                <h1 class="header-title">Athlete Performance Dashboard</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown('<h1 class="header-title">Athlete Performance Dashboard</h1>', unsafe_allow_html=True)

    # Initialize session state
    if 'sort' not in st.session_state:
        st.session_state.sort = {'column': 'Event', 'ascending': True}

    # Load data
    athletes = load_data()
    if not athletes:
        st.stop()

    # Athlete selection
    athlete = st.selectbox("Select Athlete:", list(athletes.keys()))
    df = pd.DataFrame(athletes[athlete])

    # Prepare sortable columns
    df['_time_sec'] = df['Time'].apply(time_to_seconds)
    df['_event_m'] = df['Event'].apply(event_to_meters)
    df['_date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')

    # Create sorting buttons
    columns = ['Event', 'Time', 'Category', 'Club', 'Region', 'Location', 'Date']
    cols = st.columns(7)
    for i, col in enumerate(columns):
        with cols[i]:
            if st.button(f"⇅ {col}"):
                if st.session_state.sort['column'] == col:
                    st.session_state.sort['ascending'] = not st.session_state.sort['ascending']
                else:
                    st.session_state.sort = {'column': col, 'ascending': True}

    # Apply sorting
    sort_col = st.session_state.sort['column']
    sort_asc = st.session_state.sort['ascending']
    
    try:
        sort_mapping = {
            'Event': '_event_m',
            'Time': '_time_sec', 
            'Date': '_date'
        }
        sort_by = sort_mapping.get(sort_col, sort_col)
        df = df.sort_values(sort_by, ascending=sort_asc, na_position='last')
    except Exception as e:
        st.error(f"Sorting error: {str(e)}")
        df = df.sort_values(sort_col, ascending=sort_asc, na_position='last')

    # Display table
    st.markdown(
        f'<div style="pointer-events:none; user-select:none; margin-top:0; padding-top:0">'
        f'{make_non_interactive_table(df[columns], show_header=False)}'
        f'</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()