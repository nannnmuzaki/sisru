import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
import joblib

def classify_quality(score):
    if score <= 4:
        return 'BURUK'
    elif score <= 6:
        return 'CUKUP'
    else:
        return 'BAIK'

def train_and_save():
    dataset_path = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'Sleep_health_and_lifestyle_dataset.csv')
    
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return

    df = pd.read_csv(dataset_path)

    # Reclassify target
    df['Target_Class'] = df['Quality of Sleep'].apply(classify_quality)

    # Drop columns not used for training
    # "Person ID" is excluded. "Quality of Sleep" is replaced by "Target_Class".
    X = df.drop(columns=['Person ID', 'Quality of Sleep', 'Target_Class'])
    y = df['Target_Class']

    # Categorical columns to encode
    categorical_cols = ['Gender', 'Occupation', 'BMI Category', 'Blood Pressure', 'Sleep Disorder']
    
    # We will use a dictionary of LabelEncoders to save them for inference
    encoders = {}
    
    # Handle NaN in categorical if any (especially Sleep Disorder 'None')
    for col in categorical_cols:
        df[col] = df[col].fillna('None')
        X[col] = X[col].fillna('None')
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col])
        encoders[col] = le

    # Split data (stratified as per report)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # Train Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)

    # Evaluate Random Forest
    y_pred = rf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model trained. Accuracy on test set: {accuracy:.4f}\n")
    
    print("=== Detailed Classification Report ===")
    print(classification_report(y_test, y_pred))

    # Save model and encoders
    model_data = {
        'model': rf,
        'encoders': encoders,
        'feature_names': X.columns.tolist(),
        'classes': rf.classes_.tolist()
    }
    
    model_path = os.path.join(os.path.dirname(__file__), 'rf_model.pkl')
    joblib.dump(model_data, model_path)
    print(f"Model saved to {model_path}")

if __name__ == '__main__':
    train_and_save()
