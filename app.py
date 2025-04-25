# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import pickle

# Set page configuration
st.set_page_config(page_title="Classroom Utilization Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    try:
        return pd.read_csv(r'C:\Users\LingaAdithya\OneDrive\Desktop\Spreadsheet\cleaned_class_utilization.csv')
    except FileNotFoundError:
        st.error("Error: cleaned_class_utilization.csv not found. Please run the data cleaning script.")
        st.stop()

df = load_data()

# Verify required columns
required_columns = ['Room_Number', 'Department', 'Day', 'Time_Slot_Hour', 'Occupied_Binary', 'Is_Peak_Hour', 'Room_Capacity_Score', 'Scheduling_Recommendation']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.error(f"Error: Missing columns in dataset: {missing_columns}. Please ensure the data cleaning script includes these columns.")
    st.stop()

# Load forecasts
@st.cache_data
def load_forecasts():
    try:
        with open(r'C:\Users\LingaAdithya\OneDrive\Desktop\Spreadsheet\forecasts.pkl', 'rb') as f:
            forecasts = pickle.load(f)
        if not isinstance(forecasts, dict):
            st.error("Error: forecasts.pkl does not contain a valid dictionary.")
            st.stop()
        return forecasts
    except FileNotFoundError:
        st.error("Error: forecasts.pkl not found. Please run the forecasting script.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading forecasts.pkl: {e}")
        st.stop()

forecasts = load_forecasts()

# Title and description
st.title("Classroom Utilization Dashboard")
st.markdown("**Descriptive, Predictive, and Prescriptive Analytics for Optimizing Classroom Scheduling**")

# Sidebar filters
st.sidebar.header("Filters")
departments = st.sidebar.multiselect("Select Department", options=df['Department'].unique(), default=df['Department'].unique())
days = st.sidebar.multiselect("Select Day", options=df['Day'].unique(), default=df['Day'].unique())
rooms = st.sidebar.selectbox("Select Room for Forecast", options=df['Room_Number'].unique(), index=0)

# Filter data
filtered_df = df[df['Department'].isin(departments) & df['Day'].isin(days)]
if filtered_df.empty:
    st.warning("No data available for the selected filters. Please adjust the Department or Day selections.")
    st.stop()

utilization = filtered_df.groupby(['Room_Number', 'Day', 'Day_Order'])['Occupied_Binary'].mean().reset_index()
utilization.rename(columns={'Occupied_Binary': 'Utilization_Rate'}, inplace=True)

# Descriptive Analytics
st.header("Descriptive Analytics")

# Heatmap: Utilization by Room and Day
st.subheader("Utilization by Room and Day")
heatmap_fig = px.density_heatmap(
    utilization,
    x='Day',
    y='Room_Number',
    z='Utilization_Rate',
    color_continuous_scale='RdBu',
    title='',
    category_orders={'Day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']},
    text_auto='.2%'
)
heatmap_fig.update_layout(xaxis_title='Day', yaxis_title='Room Number')
st.plotly_chart(heatmap_fig, use_container_width=True)

# Bar Chart: Utilization by Time Slot and Department
st.subheader("Utilization by Time Slot and Department")
time_slot_util = filtered_df.groupby(['Time_Slot_Hour', 'Department', 'Is_Peak_Hour'])['Occupied_Binary'].mean().reset_index()
time_slot_util.rename(columns={'Occupied_Binary': 'Utilization_Rate'}, inplace=True)
bar_fig = px.bar(
    time_slot_util,
    x='Time_Slot_Hour',
    y='Utilization_Rate',
    color='Is_Peak_Hour',
    facet_row='Department',
    title='',
    labels={'Time_Slot_Hour': 'Time Slot (Hour)', 'Utilization_Rate': 'Utilization Rate'},
    height=800
)
bar_fig.update_layout(yaxis_tickformat='.0%')
st.plotly_chart(bar_fig, use_container_width=True)

# Pie Chart: Course Distribution
st.subheader("Course Distribution")
course_dist = filtered_df[filtered_df['Course Code'].notnull()]['Course Code'].value_counts().head(10).reset_index()
course_dist.columns = ['Course Code', 'Count']
if course_dist.empty:
    st.info("No courses available for the selected filters.")
else:
    pie_fig = px.pie(
        course_dist,
        names='Course Code',
        values='Count',
        title=''
    )
    st.plotly_chart(pie_fig, use_container_width=True)

# Predictive Analytics
st.header("Predictive Analytics")
st.subheader(f"Utilization Forecast for {rooms}")
if forecasts is None or not isinstance(forecasts, dict):
    st.error("Error: Forecasts not loaded correctly. Please ensure 'forecasts.pkl' is valid.")
elif rooms not in forecasts:
    st.info(f"No forecast available for {rooms}.")
else:
    forecast_data = forecasts[rooms]
    forecast_fig = px.line(
        forecast_data,
        x='ds',
        y=['yhat', 'yhat_lower', 'yhat_upper'],
        title='',
        labels={'ds': 'Date', 'value': 'Utilization Rate'}
    )
    forecast_fig.update_layout(yaxis_tickformat='.0%')
    st.plotly_chart(forecast_fig, use_container_width=True)

# Prescriptive Analytics
st.header("Prescriptive Analytics")

# Stacked Bar: Room Capacity Score
st.subheader("Room Capacity Utilization Score")
capacity_dist = filtered_df.groupby(['Room_Number', 'Room_Capacity_Score']).size().unstack(fill_value=0).reset_index()
# Ensure all expected columns exist
score_columns = ['Underutilized', 'Optimal', 'Overutilized']
for col in score_columns:
    if col not in capacity_dist.columns:
        capacity_dist[col] = 0
# Use only available columns for plotting
y_columns = [col for col in score_columns if col in capacity_dist.columns]
if not y_columns:
    st.info("No room capacity data available for the selected filters.")
else:
    stack_fig = px.bar(
        capacity_dist,
        x='Room_Number',
        y=y_columns,
        title='',
        labels={'value': 'Count', 'Room_Number': 'Room Number'},
        height=500
    )
    st.plotly_chart(stack_fig, use_container_width=True)

# Gantt Chart: Detailed Schedule
st.subheader("Detailed Schedule for Under/Overutilized Rooms")
gantt_data = filtered_df[filtered_df['Room_Capacity_Score'].isin(['Underutilized', 'Overutilized'])]
if gantt_data.empty:
    st.info("No under/overutilized rooms for the selected filters.")
else:
    gantt_fig = px.scatter(
        gantt_data,
        x='Time_Slot_Hour',
        y='Room_Number',
        color='Occupied_Binary',
        facet_col='Day',
        title='',
        hover_data=['Course Code', 'Faculty'],
        height=600
    )
    gantt_fig.update_traces(marker=dict(size=12))
    st.plotly_chart(gantt_fig, use_container_width=True)

# Recommendations
st.subheader("Scheduling Recommendations")
recommendations = filtered_df.groupby(['Room_Number', 'Room_Capacity_Score', 'Scheduling_Recommendation']).size().reset_index(name='Count')
st.markdown(recommendations[['Room_Number', 'Room_Capacity_Score', 'Scheduling_Recommendation']].to_markdown(index=False))