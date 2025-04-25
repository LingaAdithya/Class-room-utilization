# generate_forecasts.py
import pandas as pd
from prophet import Prophet
import pickle

# Load cleaned data
df = pd.read_csv(r'C:\Users\LingaAdithya\OneDrive\Desktop\Spreadsheet\cleaned_class_utilization.csv')
utilization = df.groupby(['Room_Number', 'Day', 'Day_Order'])['Occupied_Binary'].mean().reset_index()
utilization.rename(columns={'Occupied_Binary': 'Utilization_Rate'}, inplace=True)

# Generate forecasts for each room
forecasts = {}
for room in utilization['Room_Number'].unique():
    room_data = utilization[utilization['Room_Number'] == room][['Day_Order', 'Utilization_Rate']].copy()
    if len(room_data) >= 2:  # Ensure sufficient data points
        room_data['ds'] = pd.date_range(start='2025-04-21', periods=len(room_data), freq='D')
        room_data['y'] = room_data['Utilization_Rate']
        room_data = room_data[['ds', 'y']]
        
        model = Prophet(daily_seasonality=True)
        model.fit(room_data)
        future = model.make_future_dataframe(periods=5)
        forecasts[room] = model.predict(future)
    else:
        print(f"Skipping forecast for {room}: insufficient data points.")

# Save forecasts to a pickle file
with open(r'C:\Users\LingaAdithya\OneDrive\Desktop\Spreadsheet\forecasts.pkl', 'wb') as f:
    pickle.dump(forecasts, f)
print("Forecasts generated and saved as 'forecasts.pkl'.")