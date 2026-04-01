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
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}

h1 {
    text-align: center;
    font-size: 3rem;
    font-weight: bold;
    background: -webkit-linear-gradient(#00C9A7, #92FE9D);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

section[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
}

[data-testid="metric-container"] {
    background: rgba(255,255,255,0.08);
    border-radius: 15px;
    padding: 15px;
    backdrop-filter: blur(10px);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# TITLE
# -----------------------------
st.markdown("<h1>🌦️ Weather Anomaly Intelligence Dashboard</h1>", unsafe_allow_html=True)

# -----------------------------
# DATA SOURCE
# -----------------------------
st.sidebar.header("📂 Data Source")
option = st.sidebar.radio("Choose Data Source", ["Use Default Dataset", "Upload CSV"])

if option == "Use Default Dataset":
    try:
        data = pd.read_csv("weather.csv")
    except:
        st.error("weather.csv not found")
        st.stop()
else:
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file:
        data = pd.read_csv(uploaded_file)
    else:
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
data['Temperature'] = pd.to_numeric(data['Temperature'], errors='coerce')
data['Rainfall'] = pd.to_numeric(data['Rainfall'], errors='coerce')

data = data.dropna()

data['Month'] = data['Date'].dt.month

def get_season(m):
    return ("Winter" if m in [12,1,2] else
            "Summer" if m in [3,4,5] else
            "Monsoon" if m in [6,7,8,9] else
            "Post-Monsoon")

data['Season'] = data['Month'].apply(get_season)

# -----------------------------
# ANOMALY DETECTION
# -----------------------------
monthly_avg = data.groupby('Month')[['Temperature','Rainfall']].mean()
seasonal_avg = data.groupby('Season')[['Temperature','Rainfall']].mean()

def detect(row):
    if abs(row['Temperature'] - monthly_avg.loc[row['Month'],'Temperature']) > 5:
        return "Temp Anomaly"
    elif abs(row['Rainfall'] - monthly_avg.loc[row['Month'],'Rainfall']) > 10:
        return "Rain Anomaly"
    elif abs(row['Temperature'] - seasonal_avg.loc[row['Season'],'Temperature']) > 5:
        return "Temp Anomaly (Seasonal)"
    elif abs(row['Rainfall'] - seasonal_avg.loc[row['Season'],'Rainfall']) > 10:
        return "Rain Anomaly (Seasonal)"
    return "Normal"

data['Status'] = data.apply(detect, axis=1)

# -----------------------------
# FILTERS
# -----------------------------
start = st.sidebar.date_input("Start Date", data['Date'].min())
end = st.sidebar.date_input("End Date", data['Date'].max())

filtered = data[(data['Date']>=pd.to_datetime(start)) &
                (data['Date']<=pd.to_datetime(end))].copy()

if len(filtered) < 3:
    st.warning("Not enough data")
    st.stop()

# -----------------------------
# SMOOTHING
# -----------------------------
filtered = filtered.sort_values("Date")

filtered['Temp_Smooth'] = filtered['Temperature'].rolling(window=3, min_periods=1).mean()
filtered['Rain_Smooth'] = filtered['Rainfall'].rolling(window=3, min_periods=1).mean()

filtered['Highlight'] = filtered['Status'].apply(
    lambda x: "Anomaly" if "Anomaly" in x else "Normal"
)

# -----------------------------
# METRICS
# -----------------------------
c1,c2,c3 = st.columns(3)
c1.metric("🌡️ Avg Temp", f"{filtered['Temperature'].mean():.2f}°C")
c2.metric("🌧️ Total Rain", f"{filtered['Rainfall'].sum():.2f} mm")
c3.metric("⚠️ Anomalies", (filtered['Status']!="Normal").sum())

# -----------------------------
# TEMPERATURE GRAPH
# -----------------------------
st.subheader("🌡️ Temperature")

fig1 = px.line(filtered, x='Date', y='Temp_Smooth')
fig1.update_traces(line=dict(width=4))

fig1.add_scatter(
    x=filtered[filtered['Highlight']=="Anomaly"]['Date'],
    y=filtered[filtered['Highlight']=="Anomaly"]['Temp_Smooth'],
    mode='markers',
    marker=dict(size=8, color='red'),
    name='Anomaly'
)

fig1.update_layout(template="plotly_dark")
st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# RAIN GRAPH
# -----------------------------
st.subheader("🌧️ Rainfall")

fig2 = px.line(filtered, x='Date', y='Rain_Smooth')
fig2.update_traces(line=dict(width=4))

fig2.add_scatter(
    x=filtered[filtered['Highlight']=="Anomaly"]['Date'],
    y=filtered[filtered['Highlight']=="Anomaly"]['Rain_Smooth'],
    mode='markers',
    marker=dict(size=8, color='orange'),
    name='Anomaly'
)

fig2.update_layout(template="plotly_dark")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# ANOMALY BAR GRAPH
# -----------------------------
st.subheader("⚠️ Anomaly Distribution")

anomaly_counts = filtered['Status'].value_counts().reset_index()
anomaly_counts.columns = ['Status', 'Count']

fig3 = px.bar(anomaly_counts, x='Status', y='Count', text='Count')

fig3.update_traces(textposition='outside')

fig3.update_layout(
    template="plotly_dark",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# TABLE
# -----------------------------
st.subheader("📋 Data")
st.dataframe(filtered)

# -----------------------------
# DOWNLOAD
# -----------------------------
st.download_button(
    "⬇️ Download CSV",
    filtered.to_csv(index=False),
    "result.csv"
)
