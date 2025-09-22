import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import pickle
import time

# Load CSV data
import os
data_path = os.path.join(os.path.dirname(__file__), 'data.csv')
try:
    df = pd.read_csv(data_path)
    if len(df) < 5:
        print("Not enough data for training")
        exit(1)
    print(f"Loaded {len(df)} rows of training data")
except FileNotFoundError:
    print(f"Data file not found at {data_path}")
    exit(1)

# Preprocessing and training function
def preprocess_and_train(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute
    
    le = LabelEncoder()
    df['scheduling_model_label'] = le.fit_transform(df['scheduling_model'])
    
    features = df[['hour', 'minute', 'cars_present', 'emergency_vehicle']]
    labels = df['scheduling_model_label']
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(features)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, labels, test_size=0.25, random_state=42, stratify=labels)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    
    print(classification_report(
        y_test, y_pred, 
        labels=le.transform(le.classes_), 
        target_names=le.classes_, zero_division=0))
    
    trained_objects = {'model': model, 'scaler': scaler, 'label_encoder': le}
    model_path = os.path.join(os.path.dirname(__file__), 'traffic_scheduler_model.pkl')
    temp_path = model_path + '.tmp'
    
    # Write to temp file first, then atomic rename
    with open(temp_path, 'wb') as f:
        pickle.dump(trained_objects, f)
    
    # Atomic rename to prevent read/write conflicts
    os.rename(temp_path, model_path)
    print(f"Model saved to {model_path}")
    
    return trained_objects

if __name__ == '__main__':
    trained_objs = preprocess_and_train(df)

# Function to predict scheduling model
def predict_scheduling(timestamp, cars_present, emergency_vehicle):
    model_path = os.path.join(os.path.dirname(__file__), 'traffic_scheduler_model.pkl')
    
    # Retry logic for file reading
    for attempt in range(3):
        try:
            with open(model_path, 'rb') as f:
                objs = pickle.load(f)
            break
        except (FileNotFoundError, EOFError, pickle.UnpicklingError) as e:
            if attempt == 2:
                raise e
            time.sleep(0.1)  # Brief delay before retry
    
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

# Example usage when run directly
if __name__ == '__main__':
    try:
        print(predict_scheduling('2025-09-21T19:08:55', 23, 0))
    except Exception as e:
        print(f"Error: {e}")