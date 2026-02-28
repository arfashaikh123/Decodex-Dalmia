import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page Config
st.set_page_config(page_title="VoltRide Strategic Dashboard", layout="wide", initial_sidebar_state="expanded")

# Load Data
@st.cache_data
def load_data():
    file_path = "d:/ARFA PROJECTS/Decodex Dalmia/DecodeX_VoltRide_Dataset.xlsx"
    xls = pd.ExcelFile(file_path)
    rides = pd.read_excel(xls, 'Ride_Level_Data')
    drivers = pd.read_excel(xls, 'Driver_Data')
    demand = pd.read_excel(xls, 'Zone_Hour_Demand')
    charging = pd.read_excel(xls, 'Charging_Stations')
    
    # Preprocessing
    rides['Is_Completed'] = rides['Ride_Status'] == 'Completed'
    return rides, drivers, demand, charging

try:
    rides, drivers, demand, charging = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar Filters
st.sidebar.header("Operational Filters")
selected_city = st.sidebar.selectbox("Select City", ["All"] + list(rides['City'].unique()))

if selected_city != "All":
    filtered_rides = rides[rides['City'] == selected_city]
    filtered_demand = demand[demand['City'] == selected_city]
    filtered_charging = charging[charging['City'] == selected_city]
else:
    filtered_rides = rides
    filtered_demand = demand
    filtered_charging = charging

# KPI Cards
st.title("VoltRide Strategic Command Center")

col1, col2, col3, col4 = st.columns(4)
total_requests = len(filtered_rides)
completion_rate = filtered_rides['Is_Completed'].mean()
avg_surge = filtered_rides['Surge_Multiplier'].mean()
revenue_loss = filtered_rides[~filtered_rides['Is_Completed']]['Estimated_Fare'].sum()

col1.metric("Total Requests", f"{total_requests:,}")
col2.metric("Completion Rate", f"{completion_rate:.1%}", delta_color="normal" if completion_rate > 0.8 else "inverse")
col3.metric("Avg Surge Multiplier", f"{avg_surge:.2f}x")
col4.metric("Est. Revenue Loss", f"₹{revenue_loss:,.0f}", delta_color="inverse")

# Main Dashboard Tabs
tab1, tab2, tab3 = st.tabs(["Demand Stress", "Fleet Efficiency", "Simulation Lab"])

with tab1:
    st.subheader("Demand-Supply Stress Map")
    
    # Chart 1: Stress Scatter
    stress_data = filtered_rides.groupby(['Pickup_Zone', 'Hour']).agg(
        Requests=('Ride_ID', 'count'),
        Completion=('Is_Completed', 'mean'),
        Surge=('Surge_Multiplier', 'mean')
    ).reset_index()
    
    stress_data = stress_data[stress_data['Requests'] >= 3]
    
    fig_stress = px.scatter(
        stress_data, x="Surge", y="Completion", size="Requests", color="Hour",
        hover_data=["Pickup_Zone"], title="Stress Map: Surge vs. Completion (Bubble Size = Demand)",
        color_continuous_scale="RdYlGn_r"
    )
    fig_stress.add_hrect(y0=0, y1=0.5, line_width=0, fillcolor="red", opacity=0.1, annotation_text="Critical Failure Zone")
    st.plotly_chart(fig_stress, use_container_width=True)
    
    # Chart 2: Hourly Trends
    st.subheader("Hourly Reliability Trend")
    hourly_trend = filtered_rides.groupby('Hour')['Is_Completed'].mean().reset_index()
    fig_trend = px.line(hourly_trend, x='Hour', y='Is_Completed', title="Completion Rate by Hour", markers=True)
    fig_trend.update_layout(yaxis_range=[0, 1])
    st.plotly_chart(fig_trend, use_container_width=True)

with tab2:
    st.subheader("Fleet utilization & Charging")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("##### Zone Efficiency (Oversupply Check)")
        eff_data = filtered_rides.groupby('Pickup_Zone').agg(
            Requests=('Ride_ID', 'count'),
            Surge=('Surge_Multiplier', 'mean')
        ).reset_index()
        
        fig_eff = px.bar(eff_data.sort_values('Surge'), x='Pickup_Zone', y='Surge', color='Requests',
                         title="Avg Surge by Zone (Low Surge + High Vol = Oversupply)")
        st.plotly_chart(fig_eff, use_container_width=True)
        
    with col_b:
        st.markdown("##### Charging Wait Times")
        fig_charge = px.bar(filtered_charging.sort_values('Avg_Wait_Time_Min', ascending=False).head(10),
                            x='Station_ID', y='Avg_Wait_Time_Min', color='Avg_Wait_Time_Min',
                            title="Top 10 Congested Stations", color_continuous_scale='Reds')
        st.plotly_chart(fig_charge, use_container_width=True)

with tab3:
    st.subheader("Advanced Simulation: Peak-Shifting Impact")
    
    st.markdown("Adjust the slider to simulate the impact of moving demand from Peak to Off-Peak.")
    shift_pct = st.slider("Shift % of Demand from Peak (12-14h) to Off-Peak", 0, 50, 15)
    
    # Simple logic: Reduce peak volume, increase completion rate linearly
    # Assume 1% shift improves completion by 0.5% in stress zones
    
    sim_completion = completion_rate * (1 + (shift_pct * 0.005))
    sim_revenue_recovered = revenue_loss * (shift_pct / 100) * 0.6 # recovering 60% of lost revenue
    
    c1, c2 = st.columns(2)
    c1.metric("Projected New Completion Rate", f"{min(sim_completion, 1.0):.1%}", f"+{(sim_completion - completion_rate)*100:.1f} pts")
    c2.metric("Projected Revenue Recovered", f"₹{sim_revenue_recovered:,.0f}")
    
    st.info("Simulation assumes linear elasticity between demand reduction and service quality improvement.")

st.sidebar.markdown("---")
st.sidebar.info("Generated by VoltRide Analytics Engine")
