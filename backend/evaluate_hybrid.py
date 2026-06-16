import os
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split
from cf_engine import CFEngine
from rf_model import RFModel

def classify_quality(score):
    if score <= 4:
        return 'BURUK'
    elif score <= 6:
        return 'CUKUP'
    else:
        return 'BAIK'

def evaluate_hybrid_system():
    dataset_path = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'Sleep_health_and_lifestyle_dataset.csv')
    if not os.path.exists(dataset_path):
        print("Dataset not found!")
        return

    df = pd.read_csv(dataset_path)
    df['Target_Class'] = df['Quality of Sleep'].apply(classify_quality)
    
    # Fill NaNs in categorical columns just like training
    categorical_cols = ['Gender', 'Occupation', 'BMI Category', 'Blood Pressure', 'Sleep Disorder']
    for col in categorical_cols:
        df[col] = df[col].fillna('None')

    # Fix dataset string mismatch for CF engine: 
    # The dataset uses "Normal" or "Normal Weight". CF engine specifically expects "Normal Weight".
    # (Though CF engine handles this, it's best to be consistent)
    df['BMI Category'] = df['BMI Category'].replace('Normal', 'Normal Weight')

    # Initialize engines
    cf_engine = CFEngine()
    rf_model = RFModel()
    
    if not rf_model.model:
        print("RF model not found! Please run train_model.py first.")
        return

    # Split data exactly like in train_model.py to avoid data leakage
    df_train, df_test = train_test_split(df, test_size=0.2, random_state=42, stratify=df['Target_Class'])

    y_true = []
    y_pred_cf = []
    y_pred_rf = []
    y_pred_hybrid = []

    print(f"Evaluating only on the Test Set ({len(df_test)} rows) against CF, RF, and Hybrid Engine...\n")

    for index, row in df_test.iterrows():
        # Target
        true_class = row['Target_Class']
        y_true.append(true_class)
        
        # 1. CF Engine Input
        cf_features = {
            "sleep_duration": row['Sleep Duration'],
            "stress_level": row['Stress Level'],
            "physical_activity": row['Physical Activity Level'],
            "bmi_category": row['BMI Category'],
            "heart_rate": row['Heart Rate'],
            "sleep_disorder": row['Sleep Disorder'],
            "blood_pressure": row['Blood Pressure']
        }
        cf_result = cf_engine.evaluate(cf_features)
        y_pred_cf.append(cf_result['class'])
        
        # 2. RF Model Input
        rf_features = {
            "Gender": row['Gender'],
            "Age": row['Age'],
            "Occupation": row['Occupation'],
            "Sleep Duration": row['Sleep Duration'],
            "Physical Activity Level": row['Physical Activity Level'],
            "Stress Level": row['Stress Level'],
            "BMI Category": row['BMI Category'],
            "Blood Pressure": row['Blood Pressure'],
            "Heart Rate": row['Heart Rate'],
            "Daily Steps": row['Daily Steps'],
            "Sleep Disorder": row['Sleep Disorder']
        }
        rf_result = rf_model.predict_proba(rf_features)
        rf_probs = rf_result['probabilities']
        
        # Best RF class is the one with max probability
        rf_class = rf_result['prediction']
        y_pred_rf.append(rf_class)
        
        # 3. Hybrid Engine
        hybrid_result = cf_engine.combine_with_rf(cf_result, rf_probs)
        y_pred_hybrid.append(hybrid_result['final_class'])

    # Print Results
    print("=========================================")
    print(" 1. EXPERT SYSTEM ONLY (Certainty Factor)")
    print("=========================================")
    print(f"Accuracy: {accuracy_score(y_true, y_pred_cf):.4f}")
    print(classification_report(y_true, y_pred_cf))

    print("\n=========================================")
    print(" 2. MACHINE LEARNING ONLY (Random Forest)")
    print("=========================================")
    print(f"Accuracy: {accuracy_score(y_true, y_pred_rf):.4f}")
    print(classification_report(y_true, y_pred_rf))

    print("\n=========================================")
    print(" 3. HYBRID ENGINE (0.4 CF + 0.6 RF)")
    print("=========================================")
    print(f"Accuracy: {accuracy_score(y_true, y_pred_hybrid):.4f}")
    print(classification_report(y_true, y_pred_hybrid))

if __name__ == '__main__':
    evaluate_hybrid_system()
