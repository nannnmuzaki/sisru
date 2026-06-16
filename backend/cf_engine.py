import json

class CFEngine:
    def __init__(self):
        # Define 16 rules from the expert knowledge base
        self.rules = [
            # BURUK
            {
                "id": "R01",
                "output": "BURUK",
                "cf": 0.80,
                "conditions": lambda f: f['sleep_duration'] < 6 and f['stress_level'] >= 7,
                "desc": "Durasi < 6 jam AND Stres ≥ 7"
            },
            {
                "id": "R02",
                "output": "BURUK",
                "cf": 0.75,
                "conditions": lambda f: f['bmi_category'] == 'Obese' and f['sleep_duration'] < 6,
                "desc": "BMI = Obese AND Durasi < 6 jam"
            },
            {
                "id": "R03",
                "output": "BURUK",
                "cf": 0.90,
                "conditions": lambda f: f['sleep_disorder'] == 'Insomnia',
                "desc": "Sleep Disorder = Insomnia"
            },
            {
                "id": "R04",
                "output": "BURUK",
                "cf": 0.85,
                "conditions": lambda f: f['sleep_disorder'] == 'Sleep Apnea' and f['bmi_category'] == 'Obese',
                "desc": "Sleep Disorder = Sleep Apnea AND BMI = Obese"
            },
            {
                "id": "R05",
                "output": "BURUK",
                "cf": 0.72,
                "conditions": lambda f: f['heart_rate'] > 80 and f['stress_level'] >= 7,
                "desc": "Heart Rate > 80 bpm AND Stres ≥ 7"
            },
            {
                "id": "R06",
                "output": "BURUK",
                "cf": 0.78,
                "conditions": lambda f: f['sleep_duration'] < 6 and f['stress_level'] >= 7 and f['physical_activity'] < 30,
                "desc": "Durasi < 6 jam AND Stres ≥ 7 AND Aktivitas < 30 mnt"
            },
            # CUKUP
            {
                "id": "R07",
                "output": "CUKUP",
                "cf": 0.65,
                "conditions": lambda f: 6 <= f['sleep_duration'] <= 6.9 and 5 <= f['stress_level'] <= 6,
                "desc": "Durasi 6–6.9 jam AND Stres 5–6"
            },
            {
                "id": "R08",
                "output": "CUKUP",
                "cf": 0.60,
                "conditions": lambda f: f['bmi_category'] == 'Overweight' and 30 <= f['physical_activity'] <= 60 and f['stress_level'] <= 6,
                "desc": "BMI = Overweight AND Aktivitas 30–60 mnt AND Stres ≤ 6"
            },
            {
                "id": "R09",
                "output": "CUKUP",
                "cf": 0.62,
                "conditions": lambda f: 6 <= f['sleep_duration'] <= 6.9 and f['physical_activity'] < 30 and f['stress_level'] <= 6,
                "desc": "Durasi 6–6.9 jam AND Aktivitas < 30 mnt AND Stres ≤ 6"
            },
            {
                "id": "R10",
                "output": "CUKUP",
                "cf": 0.68,
                "conditions": lambda f: f['sleep_disorder'] == 'None' and 6 <= f['sleep_duration'] <= 6.9 and f['bmi_category'] == 'Normal Weight',
                "desc": "Sleep Disorder = None AND Durasi 6–6.9 jam AND BMI Normal"
            },
            {
                "id": "R11",
                "output": "CUKUP",
                "cf": 0.58,
                "conditions": lambda f: 60 <= f['heart_rate'] <= 80 and 5 <= f['stress_level'] <= 6 and 6 <= f['sleep_duration'] <= 6.9,
                "desc": "Heart Rate 60–80 bpm AND Stres 5–6 AND Durasi 6–6.9 jam"
            },
            # BAIK
            {
                "id": "R12",
                "output": "BAIK",
                "cf": 0.85,
                "conditions": lambda f: f['sleep_duration'] >= 7 and f['physical_activity'] > 60,
                "desc": "Durasi ≥ 7 jam AND Aktivitas > 60 mnt"
            },
            {
                "id": "R13",
                "output": "BAIK",
                "cf": 0.88,
                "conditions": lambda f: f['bmi_category'] == 'Normal Weight' and f['stress_level'] <= 4 and f['physical_activity'] > 60,
                "desc": "BMI Normal AND Stres ≤ 4 AND Aktivitas > 60 mnt"
            },
            {
                "id": "R14",
                "output": "BAIK",
                "cf": 0.82,
                "conditions": lambda f: f['stress_level'] <= 4 and f['physical_activity'] > 60 and 60 <= f['heart_rate'] <= 80,
                "desc": "Stres ≤ 4 AND Aktivitas > 60 mnt AND Heart Rate 60–80 bpm"
            },
            {
                "id": "R15",
                "output": "BAIK",
                "cf": 0.80,
                "conditions": lambda f: f['sleep_disorder'] == 'None' and f['sleep_duration'] >= 7 and 60 <= f['heart_rate'] <= 80,
                "desc": "Sleep Disorder = None AND Durasi ≥ 7 jam AND Heart Rate 60–80 bpm"
            },
            {
                "id": "R16",
                "output": "BAIK",
                "cf": 0.92,
                "conditions": lambda f: f['sleep_duration'] >= 7 and f['stress_level'] <= 4 and f['bmi_category'] == 'Normal Weight' and f['physical_activity'] > 60,
                "desc": "Durasi ≥ 7 jam AND Stres ≤ 4 AND BMI Normal AND Aktivitas > 60 mnt"
            }
        ]

    def evaluate(self, features):
        """
        features is a dict:
        {
            'sleep_duration': float,
            'stress_level': int,
            'physical_activity': int,
            'bmi_category': str ('Normal Weight', 'Overweight', 'Obese'),
            'heart_rate': int,
            'sleep_disorder': str ('None', 'Insomnia', 'Sleep Apnea')
        }
        Wait, in the dataset BMI is 'Normal Weight', not 'Normal'. We will use 'Normal Weight'.
        """
        cf_scores = {"BAIK": 0.0, "CUKUP": 0.0, "BURUK": 0.0}
        fired_rules = []

        for rule in self.rules:
            # evaluate condition
            try:
                if rule["conditions"](features):
                    output_class = rule["output"]
                    old_cf = cf_scores[output_class]
                    new_cf = old_cf + rule["cf"] * (1 - old_cf)
                    cf_scores[output_class] = new_cf
                    fired_rules.append({"id": rule["id"], "desc": rule["desc"], "cf_added": rule["cf"]})
            except KeyError as e:
                # Missing feature, skip
                pass

        best_class = "CUKUP" # Default fallback
        best_cf = 0.0
        
        for k, v in cf_scores.items():
            if v > best_cf:
                best_cf = v
                best_class = k

        return {
            "class": best_class,
            "cf_value": best_cf,
            "all_scores": cf_scores,
            "fired_rules": fired_rules
        }

    def combine_with_rf(self, cf_result, rf_probs, alpha=0.4):
        """
        cf_result: output from evaluate()
        rf_probs: dict e.g. {"BAIK": 0.1, "CUKUP": 0.2, "BURUK": 0.7}
        alpha: weight for CF. (1-alpha) is weight for RF.
        """
        combined_scores = {}
        for cls in ["BAIK", "CUKUP", "BURUK"]:
            cf_val = cf_result["all_scores"].get(cls, 0.0)
            rf_val = rf_probs.get(cls, 0.0)
            score = alpha * cf_val + (1 - alpha) * rf_val
            combined_scores[cls] = score
        
        best_class = max(combined_scores, key=combined_scores.get)
        
        return {
            "final_class": best_class,
            "combined_scores": combined_scores
        }
