from flask import Flask, request, jsonify, send_from_directory
import os
import json
from models import db, Consultation, Result
from cf_engine import CFEngine
from rf_model import RFModel

app = Flask(__name__)

# Configure SQLite Database
db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')
# Ensure data dir exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize engines
cf_engine = CFEngine()
try:
    rf_model = RFModel()
except Exception as e:
    print(f"Warning: {e}")
    rf_model = None

@app.route('/')
def index():
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..'), 'index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "rf_loaded": rf_model is not None})

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    
    if not data or 'features' not in data:
        return jsonify({"error": "No features provided"}), 400

    features = data['features']
    
    # 1. Save Consultation to DB
    consultation = Consultation(
        name=features.get('name', 'Anonymous'),
        age=features.get('age', 25),
        gender=features.get('gender', 'Male'),
        occupation=features.get('occupation', 'Student'),
        sleep_duration=features.get('sleep_duration', 0),
        stress_level=features.get('stress_level', 0),
        physical_activity=features.get('physical_activity', 0),
        bmi_category=features.get('bmi_category', 'Normal Weight'),
        heart_rate=features.get('heart_rate', 0),
        sleep_disorder=features.get('sleep_disorder', 'None'),
        blood_pressure=features.get('blood_pressure', 'Normal'),
        daily_steps=features.get('daily_steps', 0)
    )
    db.session.add(consultation)
    db.session.commit()

    # 2. CF Engine inference
    cf_result = cf_engine.evaluate(features)

    # 3. RF Model inference
    if rf_model and rf_model.model:
        rf_result = rf_model.predict_proba(features)
    else:
        # Fallback if model not trained
        rf_result = {
            "prediction": "Unknown",
            "probabilities": {"BAIK": 0.33, "CUKUP": 0.33, "BURUK": 0.34}
        }

    # 4. Combine results
    final = cf_engine.combine_with_rf(cf_result, rf_result['probabilities'], alpha=0.4)
    final_class = final['final_class']

    # 5. Save Result to DB
    result_record = Result(
        consultation_id=consultation.id,
        cf_class=cf_result['class'],
        cf_value=cf_result['cf_value'],
        rf_class=rf_result['prediction'],
        rf_prob_baik=rf_result['probabilities'].get('BAIK', 0.0),
        rf_prob_cukup=rf_result['probabilities'].get('CUKUP', 0.0),
        rf_prob_buruk=rf_result['probabilities'].get('BURUK', 0.0),
        final_class=final_class,
        fired_rules=json.dumps(cf_result['fired_rules'])
    )
    db.session.add(result_record)
    db.session.commit()

    # 6. Return JSON response
    return jsonify({
        "consultation_id": consultation.id,
        "final_prediction": final_class,
        "cf_result": cf_result,
        "rf_result": rf_result,
        "combined_scores": final['combined_scores']
    })

@app.route('/history', methods=['GET'])
def get_history():
    consultations = Consultation.query.order_by(Consultation.created_at.desc()).all()
    history = []
    for c in consultations:
        if c.result:
            features = {
                "sleep_duration": c.sleep_duration,
                "stress_level": c.stress_level,
                "physical_activity": c.physical_activity,
                "bmi_category": c.bmi_category,
                "heart_rate": c.heart_rate,
                "sleep_disorder": c.sleep_disorder,
                "blood_pressure": c.blood_pressure
            }
            cf_res = cf_engine.evaluate(features)
            rf_probs = {
                "BAIK": c.result.rf_prob_baik,
                "CUKUP": c.result.rf_prob_cukup,
                "BURUK": c.result.rf_prob_buruk
            }
            comb = cf_engine.combine_with_rf(cf_res, rf_probs)

            history.append({
                "consultation_id": c.id,
                "date": c.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "name": c.name,
                "age": c.age,
                "gender": c.gender,
                "occupation": c.occupation,
                "sleep_duration": c.sleep_duration,
                "stress_level": c.stress_level,
                "physical_activity": c.physical_activity,
                "bmi_category": c.bmi_category,
                "heart_rate": c.heart_rate,
                "sleep_disorder": c.sleep_disorder,
                "blood_pressure": c.blood_pressure,
                "daily_steps": c.daily_steps,
                
                "final_class": comb["final_class"],
                "cf_result": cf_res,
                "rf_result": {
                    "prediction": c.result.rf_class,
                    "probabilities": rf_probs
                },
                "combined_scores": comb["combined_scores"]
            })
    return jsonify(history)

@app.route('/history/<int:consultation_id>', methods=['DELETE'])
def delete_history(consultation_id):
    consultation = Consultation.query.get(consultation_id)
    if not consultation:
        return jsonify({"error": "Consultation not found"}), 404
        
    if consultation.result:
        db.session.delete(consultation.result)
    db.session.delete(consultation)
    db.session.commit()
    return jsonify({"status": "success", "message": "Evaluation deleted"})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000, debug=True)
