# save_clean_data.py
import pandas as pd

# Load the dataset
try:
    df = pd.read_csv(r"C:\Users\LingaAdithya\OneDrive\Desktop\Spreadsheet\class utilization.csv")
except FileNotFoundError:
    print("Error: 'class_utilization.csv' not found. Please ensure the file is in the working directory.")
    raise

# Remove unnecessary columns
df = df.drop(columns=['Unnamed: 0', 's', df.columns[6], df.columns[7]])

# Rename columns for clarity
df = df.rename(columns={
    'Room No': 'Room_Number',
    'Is_Occupied_Binary': 'Occupied_Binary'
})

# Extract starting hour from Time Slot
df['Time_Slot_Hour'] = df['Time Slot'].apply(
    lambda x: int(x.split(' ')[0]) if 'AM' in x else int(x.split(' ')[0]) + 12 if 'PM' in x and x.split(' ')[0] != '12' else 12
)

# Create Day Order for sorting
day_mapping = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5}
df['Day_Order'] = df['Day'].map(day_mapping)

# Replace '-' with None for unoccupied slots
df.loc[df['Is_Occupied'] == 'No', ['Course Code', 'Faculty']] = None

# Calculate Utilization Rate per Room and Day
utilization = df.groupby(['Room_Number', 'Day', 'Day_Order'])['Occupied_Binary'].mean().reset_index()
utilization.rename(columns={'Occupied_Binary': 'Utilization_Rate'}, inplace=True)
df = df.merge(utilization, on=['Room_Number', 'Day', 'Day_Order'], how='left')

# Add Peak Hour Flag
df['Is_Peak_Hour'] = df['Time_Slot_Hour'].apply(lambda x: 'Peak' if x in [9, 10, 11, 12] else 'Non-Peak')

# Add Room Capacity Score
df['Room_Capacity_Score'] = df['Utilization_Rate'].apply(
    lambda x: 'Underutilized' if x < 0.3 else 'Overutilized' if x > 0.7 else 'Optimal'
)

# Add Scheduling Recommendation
df['Scheduling_Recommendation'] = df['Room_Capacity_Score'].map({
    'Underutilized': 'Schedule additional classes in available slots.',
    'Overutilized': 'Redistribute classes to underutilized rooms.',
    'Optimal': 'Maintain current schedule.'
})

# Save cleaned dataset
df.to_csv(r'C:\Users\LingaAdithya\OneDrive\Desktop\Spreadsheet\cleaned_class_utilization.csv', index=False)
print("Data cleaning complete. Saved as 'cleaned_class_utilization.csv'.")