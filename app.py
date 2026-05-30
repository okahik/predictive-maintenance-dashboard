import streamlit as st
import sqlite3
import pandas as pd

# 1. Configure the Web Page
st.set_page_config(page_title="AMAC Reliability Model", layout="wide")
st.title("🚨 AMAC Midstream Predictive Maintenance Dashboard")
st.write("Live MTBF monitoring and risk ranking for the municipal distribution network.")

# 2. Connect to the database and calculate MTBF
conn = sqlite3.connect('amac_midstream.db')
query = '''
    SELECT 
        s.Segment_Name,
        s.Zone_Type,
        COUNT(h.Incident_ID) AS Total_Failures,
        SUM(h.Downtime_Hours) AS Total_Downtime_Hrs,
        SUM(h.Volume_Lost_Bbls) AS Total_Volume_Lost
    FROM static_asset_data s
    LEFT JOIN historical_incidents h ON s.Asset_ID = h.Asset_ID
    GROUP BY s.Asset_ID
'''
df = pd.read_sql_query(query, conn)
TOTAL_HOURS = 43800.0
df['Operational_Uptime_Hrs'] = TOTAL_HOURS - df['Total_Downtime_Hrs']
df['MTBF_Hours'] = (df['Operational_Uptime_Hrs'] / df['Total_Failures']).round(1)
df['Total_Volume_Lost'] = df['Total_Volume_Lost'].round(1)
df = df.sort_values(by='MTBF_Hours', ascending=True)
conn.close()

# 3. Create the Top Metrics Dashboard
st.subheader("System Overview (5-Year Baseline)")
col1, col2, col3 = st.columns(3)
col1.metric("Critical Risk Asset", df.iloc[0]['Segment_Name'])
col2.metric("Total System Volume Lost (Bbls)", f"{df['Total_Volume_Lost'].sum():,.1f}")
col3.metric("Average Network MTBF (Hrs)", f"{df['MTBF_Hours'].mean():,.1f}")

st.divider()

# 4. Display the Interactive Tables and Charts
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Asset Risk Ranking")
    st.write("Ranked from lowest MTBF (High Risk) to highest MTBF (Low Risk).")
    st.dataframe(df[['Segment_Name', 'Zone_Type', 'MTBF_Hours', 'Total_Failures']], use_container_width=True)

with col_right:
    st.subheader("Volume Lost per Segment")
    st.bar_chart(data=df, x='Segment_Name', y='Total_Volume_Lost', color="#ff4b4b")
