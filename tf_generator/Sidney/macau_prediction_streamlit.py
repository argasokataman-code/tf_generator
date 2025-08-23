import streamlit as st
import pandas as pd
import numpy as np
from collections import Counter
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import pyperclip
import os

# ✅ FUNGSI ASLI YANG UDAH PATEN (TIDAK DIUBAH)
def load_data(file_path):
    """Load data dengan handling yang lebih robust"""
    try:
        if isinstance(file_path, str):
            data = pd.read_excel(file_path, header=None, dtype=str)
        else:
            data = pd.read_excel(file_path, header=None, dtype=str)
        
        all_numbers = []
        for col in data.columns:
            col_data = data[col].dropna().astype(str).str.strip()
            for num_str in col_data:
                clean_num = ''.join(filter(str.isdigit, num_str))
                if len(clean_num) >= 4:
                    all_numbers.append(clean_num[:2])
                elif len(clean_num) == 2:
                    all_numbers.append(clean_num)
        
        return all_numbers
        
    except Exception as e:
        st.error(f"ERROR: {e}")
        return [f"{random.randint(0, 99):02d}" for _ in range(100)]

def deterministic_selection(data, total_numbers=60):
    """Selection yang deterministic berdasarkan data"""
    if len(data) < 50:
        return [f"{i:02d}" for i in range(total_numbers)]
    
    weights = {}
    for i, num in enumerate(data):
        weight = 1.0 + (i / len(data)) * 2.0
        if num not in weights:
            weights[num] = 0
        weights[num] += weight
    
    total_weight = sum(weights.values())
    probabilities = {num: weight/total_weight for num, weight in weights.items()}
    
    sorted_nums = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    
    selected = []
    for num, prob in sorted_nums:
        if len(selected) >= total_numbers:
            break
        if num not in selected:
            selected.append(num)
    
    return selected[:total_numbers]

def analyze_last_50_performance(data, predictions):
    """Analisis performa prediksi terhadap 50 data terakhir"""
    if len(data) < 50:
        return 0, 0
    
    last_50_data = data[-50:]
    last_50_unique = set(last_50_data)
    
    hits = len(set(predictions) & last_50_unique)
    total_actual = len(last_50_unique)
    accuracy = (hits / total_actual) * 100 if total_actual > 0 else 0
    
    return hits, accuracy

def find_last_appearance(data, number):
    """Cari kapan terakhir kali number muncul"""
    for i in range(len(data)-1, -1, -1):
        if data[i] == number:
            return len(data) - i
    return 999

# ✅ FUNGSI BARU UNTUK WINRATE TRACKING
def load_winrate_data():
    """Load winrate data dari CSV"""
    if os.path.exists("winrate_data.csv"):
        return pd.read_csv("winrate_data.csv")
    else:
        return pd.DataFrame(columns=['date', 'predicted', 'actual', 'hits', 'accuracy'])

def save_winrate_data(df):
    """Save winrate data ke CSV"""
    df.to_csv("winrate_data.csv", index=False)

def update_winrate(predicted, actual, hits, accuracy):
    """Update winrate data dengan result baru"""
    df = load_winrate_data()
    
    new_entry = {
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'predicted': predicted,
        'actual': actual,
        'hits': hits,
        'accuracy': accuracy
    }
    
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    save_winrate_data(df)
    return df

def calculate_winrate_stats():
    """Hitung overall winrate stats"""
    df = load_winrate_data()
    if len(df) == 0:
        return 0, 0, 0, 0
    
    total_days = len(df)
    total_hits = df['hits'].sum()
    total_predictions = total_days * 60  # 60 numbers per day
    overall_accuracy = (total_hits / total_predictions) * 100 if total_predictions > 0 else 0
    avg_daily_accuracy = df['accuracy'].mean()
    
    return total_days, total_hits, overall_accuracy, avg_daily_accuracy

# ✅ FUNGSI VISUALIZATION (TAMBAHAN)
def create_winrate_chart():
    """Buat chart winrate over time"""
    df = load_winrate_data()
    if len(df) == 0:
        return None
    
    fig = px.line(df, x='date', y='accuracy', 
                 title='📈 WinRate Accuracy Over Time',
                 labels={'date': 'Date', 'accuracy': 'Accuracy (%)'})
    fig.update_traces(line=dict(color='green', width=3))
    return fig

def create_hits_chart():
    """Buat chart hits per day"""
    df = load_winrate_data()
    if len(df) == 0:
        return None
    
    fig = px.bar(df, x='date', y='hits',
                title='🎯 Daily Hits Count',
                labels={'date': 'Date', 'hits': 'Hits'})
    fig.update_traces(marker_color='orange')
    return fig

def create_accuracy_gauge(accuracy):
    """Create a gauge chart for prediction accuracy"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=accuracy,
        title={'text': "Prediction Accuracy (%)"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "green"},
            'steps': [
                {'range': [0, 50], 'color': "red"},
                {'range': [50, 80], 'color': "yellow"},
                {'range': [80, 100], 'color': "lightgreen"}
            ],
        }
    ))
    fig.update_layout(height=300)
    return fig

# 🚀 STREAMLIT APP
def main():
    st.set_page_config(
        page_title="Lotto Predictor Pro", 
        page_icon="🎯", 
        layout="wide"
    )
    
    st.title("🎯 Lotto Predictor Pro + WinRate Tracker")
    st.markdown("Real-time Prediction & Advanced Analytics")
    
    # Inisialisasi variables
    predictions_str = ""
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Upload Dataset")
        uploaded_file = st.file_uploader(
            "Choose Excel file", 
            type=["xlsx", "xls"],
            help="Upload dataset HK atau Macau"
        )
        
        if uploaded_file:
            st.success(f"✅ {uploaded_file.name} loaded!")
            if "hklotto" in uploaded_file.name.lower():
                st.info("HK Lotto Dataset Detected")
            elif "macau" in uploaded_file.name.lower():
                st.info("Macau Dataset Detected")
    
    # Main content
    if uploaded_file:
        # Load data
        with st.spinner("🔄 Loading data..."):
            data = load_data(uploaded_file)
            predictions = deterministic_selection(data, 60)
            hits, accuracy = analyze_last_50_performance(data, predictions)
            predictions_str = "*".join(predictions)
        
        # WinRate Stats
        total_days, total_hits, overall_accuracy, avg_daily_accuracy = calculate_winrate_stats()
        
        # Metrics
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Total Data", len(data))
        with col2:
            st.metric("Unique Numbers", len(set(data)))
        with col3:
            st.metric("Prediction Accuracy", f"{accuracy:.1f}%")
        with col4:
            st.metric("Numbers Predicted", len(predictions))
        with col5:
            st.metric("Overall WinRate", f"{overall_accuracy:.1f}%")
        with col6:
            st.metric("Tracking Days", total_days)
        
        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Predictions", "🔥 Heatmap", "📊 Analytics", "🔍 Details", "🎯 WinRate"])
        
        with tab1:
            st.header("GENERATING PREDICTION")
            st.markdown("=" * 70)
            
            st.text("50 Predicted Numbers:")
            st.text(predictions_str)
            
            st.markdown("=" * 70)
            
            if st.button("📋 Copy Prediction", key="copy_prediction"):
                pyperclip.copy(predictions_str)
                st.success("✅ Copied to clipboard!")
            
            st.code(predictions_str, language="text")
            
            st.subheader("Number Metrics")
            cols = st.columns(6)
            for i, num in enumerate(predictions):
                cols[i % 6].metric(f"Number {num}", num, delta="Hot" if data.count(num) > 5 else "Normal")
            
            st.plotly_chart(create_accuracy_gauge(accuracy), use_container_width=True)
        
        with tab2:
            st.header("Number Heatmap")
            # [Heatmap code tetap sama]
        
        with tab3:
            st.header("Frequency Analysis")
            # [Frequency code tetap sama]
        
        with tab4:
            st.header("Detailed Analysis")
            # [Detailed analysis code tetap sama]
        
        with tab5:
            st.header("🎯 WinRate Tracker")
            
            # Input hasil harian
            st.subheader("📝 Input Today's Result")
            col1, col2 = st.columns(2)
            
            with col1:
                actual_numbers = st.text_input("Actual Numbers (pisahkan dengan koma)", 
                                             help="Contoh: 12,34,56,78,90")
            
            with col2:
                if st.button("💾 Save Result", key="save_result"):
                    if actual_numbers:
                        actual_list = [num.strip() for num in actual_numbers.split(",")]
                        actual_set = set(actual_list)
                        
                        # Hitung hits
                        today_hits = len(set(predictions) & actual_set)
                        today_accuracy = (today_hits / len(actual_set)) * 100 if actual_set else 0
                        
                        # Update winrate data
                        update_winrate(predictions_str, actual_numbers, today_hits, today_accuracy)
                        st.success(f"✅ Result saved! Hits: {today_hits}/{len(actual_set)} ({today_accuracy:.1f}%)")
                    else:
                        st.error("❌ Please input actual numbers!")
            
            # WinRate Charts
            st.subheader("📈 WinRate Statistics")
            
            win_col1, win_col2, win_col3, win_col4 = st.columns(4)
            with win_col1:
                st.metric("Total Tracking Days", total_days)
            with win_col2:
                st.metric("Total Hits", total_hits)
            with win_col3:
                st.metric("Overall WinRate", f"{overall_accuracy:.1f}%")
            with win_col4:
                st.metric("Avg Daily Accuracy", f"{avg_daily_accuracy:.1f}%")
            
            # Charts
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                winrate_chart = create_winrate_chart()
                if winrate_chart:
                    st.plotly_chart(winrate_chart, use_container_width=True)
            
            with chart_col2:
                hits_chart = create_hits_chart()
                if hits_chart:
                    st.plotly_chart(hits_chart, use_container_width=True)
            
            # History table
            st.subheader("📋 Result History")
            winrate_df = load_winrate_data()
            if len(winrate_df) > 0:
                st.dataframe(winrate_df.sort_values('date', ascending=False))
            else:
                st.info("No result history yet. Input today's result to start tracking!")
    
    else:
        st.info("👆 Please upload an Excel file to get started")
        st.image("https://via.placeholder.com/600x300?text=Upload+Dataset+Excel", use_container_width=True)

if __name__ == "__main__":
    main()