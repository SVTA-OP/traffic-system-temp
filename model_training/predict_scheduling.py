import pandas as pd
import pickle

# Function to predict scheduling model (copied from your code for completeness)
def predict_scheduling(timestamp, cars_present, emergency_vehicle):
    # Load the pickled objects
    with open('traffic_scheduler_model.pkl', 'rb') as f:
        objs = pickle.load(f)
    
    # Prepare input data
    df = pd.DataFrame({
        'timestamp': [timestamp],
        'cars_present': [cars_present],
        'emergency_vehicle': [emergency_vehicle]
    })
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute
    
    X = df[['hour', 'minute', 'cars_present', 'emergency_vehicle']]
    X_scaled = objs['scaler'].transform(X)
    pred_label = objs['model'].predict(X_scaled)
    pred_sched = objs['label_encoder'].inverse_transform(pred_label)
    
    return pred_sched[0]

# Example predictions
print(predict_scheduling('2025-09-21T19:08:55', 23, 0))  # e.g., 'Round Robin'
print(predict_scheduling('2025-09-21T20:15:00', 32, 9))  # e.g., 'Priority Scheduling' if emergency
print()
print(predict_scheduling('2025-09-21T20:15:05', 13, 0))
print(predict_scheduling('2025-09-21T20:15:10', 20, 1))
print(predict_scheduling('2025-09-21T20:15:15', 2, 0))
