import pandas as pd
import pickle

# Function to predict scheduling model (copied from your code for completeness)
def predict_scheduling(timestamp, cars_present, emergency_vehicle):
    import os
    import time
    # Load the pickled objects with retry logic
    model_path = os.path.join(os.path.dirname(__file__), 'traffic_scheduler_model.pkl')
    
    for attempt in range(3):
        try:
            with open(model_path, 'rb') as f:
                objs = pickle.load(f)
            break
        except (FileNotFoundError, EOFError, pickle.UnpicklingError) as e:
            if attempt == 2:
                raise e
            time.sleep(0.1)  # Brief delay before retry
    
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

# Example predictions when run directly
if __name__ == '__main__':
    import sys
    if len(sys.argv) == 4:
        timestamp = sys.argv[1]
        cars_present = int(sys.argv[2])
        emergency_vehicle = int(sys.argv[3])
        try:
            result = predict_scheduling(timestamp, cars_present, emergency_vehicle)
            print(result)
        except Exception as e:
            print('Round Robin')  # fallback
    else:
        # Default examples
        try:
            print(predict_scheduling('2025-09-21T19:08:55', 23, 0))
            print(predict_scheduling('2025-09-21T20:15:00', 32, 1))
            print(predict_scheduling('2025-09-21T20:15:05', 13, 0))
        except Exception as e:
            print('Round Robin')
