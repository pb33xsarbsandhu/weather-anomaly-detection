import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Weather Dashboard", layout="wide")

# -----------------------------
# PREMIUM UI CSS
# -----------------------------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}

/* Title */
h1 {
    text-align: center;
    font-size: 3rem;
    font-weight: bold;
    background: -webkit-linear-gradient(#00C9A7, #92FE9D);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
}

/* Metrics */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.08);
    border-radius: 15px;
    padding: 15px;
    backdrop-filter: blur(10px);
    box-shadow: 0px 4px 20px rgba(0,0,0,0.3);
}

/* Buttons */
.stButton>button {
    border-radius: 10px;
    background: linear-gradient(45deg, #00C9A7, #92FE9D);
    color: black;
    font-weight: bold;
}

/* Spacing */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# TITLE
# -----------------------------
st.markdown("<h1>🌦️ Weather Anomaly Intelligence Dashboard</h1>", unsafe_allow_html=True)
st.markdown("### 📊 Real-time insights into temperature & rainfall anomalies")

# -----------------------------
# SIDEBAR - DATA SOURCE
# -----------------------------
st.sidebar.header("📂 Data Source")
option = st.sidebar.radio("Choose Data Source", ["Use Default Dataset", "Upload CSV"])

# -----------------------------
# LOAD DATA
# -----------------------------
if option == "Use Default Dataset":
    try:
        data = pd.read_csv("weather.csv")
        st.success("✅ Default dataset loaded successfully!")
    except:
        st.error("❌ 'weather.csv' not found in folder")
        st.stop()
else:
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        data = pd.read_csv(uploaded_file)
        st.success("✅ Uploaded dataset loaded!")
    else:
        st.warning("Please upload a CSV file")
        st.stop()

# -----------------------------
# CLEAN DATA
# -----------------------------
data.rename(columns={
    'date': 'Date',
    'temperature_2m_max': 'Temperature',
    'precipitation_sum': 'Rainfall'
}, inplace=True)

data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
data = data.dropna(subset=['Date', 'Temperature', 'Rainfall'])

data['Month'] = data['Date'].dt.month

def get_season(month):
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Monsoon"
    else:
        return "Post-Monsoon"

data['Season'] = data['Month'].apply(get_season)

# -----------------------------
# CALCULATIONS
# -----------------------------
monthly_avg = data.groupby('Month')[['Temperature', 'Rainfall']].mean()
seasonal_avg = data.groupby('Season')[['Temperature', 'Rainfall']].mean()

def detect(row):
    if abs(row['Temperature'] - monthly_avg.loc[row['Month'], 'Temperature']) > 5:
        return "Temp Anomaly"
    elif abs(row['Rainfall'] - monthly_avg.loc[row['Month'], 'Rainfall']) > 10:
        return "Rain Anomaly"
    elif abs(row['Temperature'] - seasonal_avg.loc[row['Season'], 'Temperature']) > 5:
        return "Temp Anomaly (Seasonal)"
    elif abs(row['Rainfall'] - seasonal_avg.loc[row['Season'], 'Rainfall']) > 10:
        return "Rain Anomaly (Seasonal)"
    else:
        return "Normal"

data['Status'] = data.apply(detect, axis=1)

# -----------------------------
# FILTERS
# -----------------------------
st.sidebar.header("🎛️ Filters")

if 'city' in data.columns:
    cities = st.sidebar.multiselect("Select City", data['city'].unique(), default=data['city'].unique())
    data = data[data['city'].isin(cities)]

start_date = st.sidebar.date_input("Start Date", data['Date'].min())
end_date = st.sidebar.date_input("End Date", data['Date'].max())

filtered_data = data[
    (data['Date'] >= pd.to_datetime(start_date)) &
    (data['Date'] <= pd.to_datetime(end_date))
]

# Fix warning
filtered_data = filtered_data.copy()

# -----------------------------
# METRICS
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("🌡️ Avg Temperature", f"{filtered_data['Temperature'].mean():.2f} °C")
col2.metric("🌧️ Total Rainfall", f"{filtered_data['Rainfall'].sum():.2f} mm")
col3.metric("⚠️ Anomalies Detected", (filtered_data['Status'] != "Normal").sum())

# -----------------------------
# INSIGHTS
# -----------------------------
st.markdown("### 🧠 Insights")

if (filtered_data['Status'] != "Normal").sum() > 0:
    st.warning("⚠️ Unusual weather patterns detected. Review highlighted anomalies.")
else:
    st.success("✅ Weather patterns are stable and normal.")

st.markdown("---")

# Highlight
filtered_data['Highlight'] = filtered_data['Status'].apply(
    lambda x: "Anomaly" if "Anomaly" in x else "Normal"
)

# -----------------------------
# TEMPERATURE GRAPH
# -----------------------------
st.markdown("## 🌡️ Temperature Analysis")

fig1 = px.line(
    filtered_data,
    x='Date',
    y='Temperature',
    color='Highlight',
    markers=True
)

fig1.update_layout(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# RAINFALL GRAPH
# -----------------------------
st.markdown("## 🌧️ Rainfall Analysis")

fig2 = px.line(
    filtered_data,
    x='Date',
    y='Rainfall',
    color='Highlight',
    markers=True
)

fig2.update_layout(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# ANOMALY CHART
# -----------------------------
st.markdown("## ⚠️ Anomaly Insights")

anomaly_counts = filtered_data['Status'].value_counts().reset_index()
anomaly_counts.columns = ['Status', 'Count']

fig3 = px.bar(
    anomaly_counts,
    x='Status',
    y='Count',
    text='Count'
)

fig3.update_layout(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# -----------------------------
# DATA TABLE
# -----------------------------
st.subheader("📋 Processed Data")
st.dataframe(filtered_data)

# -----------------------------
# DOWNLOAD
# -----------------------------
st.download_button(
    "⬇️ Download Result",
    filtered_data.to_csv(index=False),
    file_name="weather_analysis_result.csv"
)