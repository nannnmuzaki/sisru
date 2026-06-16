import os
import joblib
import pandas as pd

class RFModel:
    def __init__(self):
        model_path = os.path.join(os.path.dirname(__file__), 'rf_model.pkl')
        if os.path.exists(model_path):
            self.model_data = joblib.load(model_path)
            self.model = self.model_data['model']
            self.encoders = self.model_data['encoders']
            self.feature_names = self.model_data['feature_names']
            self.classes = self.model_data['classes']
        else:
            self.model_data = None
            self.model = None

    def predict_proba(self, input_dict):
        """
        Expects input_dict with keys matching feature_names.
        """
        if not self.model:
            raise Exception("Model not loaded. Please train the model first.")

        # Create DataFrame from input
        # Note: the input dict should be wrapped in a list to make a single-row dataframe
        df = pd.DataFrame([input_dict])

        # Ensure all columns are present
        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0 # Default fallback

        # Encode categorical features
        for col, le in self.encoders.items():
            if col in df.columns:
                val = df[col].iloc[0]
                # Handle unseen labels by falling back or checking classes
                if val in le.classes_:
                    df[col] = le.transform(df[col])
                else:
                    # If unseen label, assign 0 or use a 'None' representation
                    df[col] = 0

        # Predict
        X = df[self.feature_names]
        probs = self.model.predict_proba(X)[0]
        
        prob_dict = {}
        for idx, cls in enumerate(self.model.classes_):
            prob_dict[cls] = float(probs[idx])
            
        prediction = self.model.predict(X)[0]

        return {
            "prediction": prediction,
            "probabilities": prob_dict
        }
