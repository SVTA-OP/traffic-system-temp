from flask import Flask, request, jsonify
import pandas as pd
import pickle

app = Flask(__name__)

# Load once at startup
with open('traffic_scheduler_model.pkl', 'rb') as f:
    objs = pickle.load(f)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    timestamp = data['timestamp']
    cars_present = data['cars_present']
    emergency_vehicle = data['emergency_vehicle']
    
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
    pred_sched = objs['label_encoder'].inverse_transform(pred_label)[0]
    
    return jsonify({'scheduling_model': pred_sched})

if __name__ == '__main__':
    app.run(debug=True)