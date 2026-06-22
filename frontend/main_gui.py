# pyrefly: ignore [missing-import]
import os
import sys

# Fix Tcl/Tk paths for Windows python distributions (like Laragon)
if sys.platform.startswith('win'):
    tcl_dir = os.path.join(sys.base_prefix, 'tcl')
    if os.path.exists(tcl_dir):
        for d in os.listdir(tcl_dir):
            path = os.path.join(tcl_dir, d)
            if os.path.isdir(path):
                if d.startswith('tcl'):
                    os.environ['TCL_LIBRARY'] = path
                elif d.startswith('tk'):
                    os.environ['TK_LIBRARY'] = path

# pyrefly: ignore [missing-import]
import customtkinter as ctk
import requests
import tkinter.messagebox as messagebox
import tkinter.filedialog as filedialog
import json
import csv

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Sisru: Sistem Pakar Evaluasi Kualitas Tidur (Hybrid Dashboard)")
        self.geometry("1280x820")
        self.resizable(True, True)
        
        # Grid config:
        # Col 0: Sidebar (Weight 0, minsize=300)
        # Col 1: Main Content Dashboard (Weight 1)
        self.grid_columnconfigure(0, weight=0, minsize=300)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # State tracking
        self.is_preview_mode = False
        self.current_consultation_id = None

        # Value mappings (UI Indonesian -> Backend English)
        self.gender_map = {"Laki-laki": "Male", "Perempuan": "Female"}
        self.occupation_map = {
            "Software Engineer": "Software Engineer", 
            "Dokter": "Doctor", 
            "Guru": "Teacher", 
            "Pelajar/Mahasiswa": "Student", 
            "Lainnya": "Other"
        }
        self.bmi_map = {
            "Normal": "Normal Weight", 
            "Kelebihan Berat Badan": "Overweight", 
            "Obesitas": "Obese"
        }
        self.sleep_disorder_map = {
            "Tidak Ada": "None", 
            "Insomnia": "Insomnia", 
            "Sleep Apnea": "Sleep Apnea"
        }
        self.blood_pressure_map = {
            "Normal": "Normal", 
            "Meningkat": "Elevated", 
            "Tinggi": "High"
        }

        # Inverse mappings for loading history
        self.inv_gender_map = {v: k for k, v in self.gender_map.items()}
        self.inv_occupation_map = {v: k for k, v in self.occupation_map.items()}
        self.inv_bmi_map = {v: k for k, v in self.bmi_map.items()}
        self.inv_sleep_disorder_map = {v: k for k, v in self.sleep_disorder_map.items()}
        self.inv_blood_pressure_map = {v: k for k, v in self.blood_pressure_map.items()}

        # ====================
        # SIDEBAR (History)
        # ====================
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(1, weight=1)

        # Header for Sidebar
        self.sidebar_header = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(15, 5))
        self.sidebar_header.grid_columnconfigure(0, weight=1)

        self.sidebar_title = ctk.CTkLabel(self.sidebar_header, text="Riwayat", font=ctk.CTkFont(size=20, weight="bold"))
        self.sidebar_title.grid(row=0, column=0, sticky="w", padx=2)

        # "New" Button
        self.new_eval_btn = ctk.CTkButton(self.sidebar_header, text="+", width=30, font=ctk.CTkFont(size=16, weight="bold"), command=self.new_evaluation)
        self.new_eval_btn.grid(row=0, column=1, padx=2)

        # "Refresh" Button
        self.refresh_btn = ctk.CTkButton(self.sidebar_header, text="↻", width=30, font=ctk.CTkFont(size=16, weight="bold"), command=self.load_history)
        self.refresh_btn.grid(row=0, column=2, padx=2)

        # List Frame
        self.history_list_frame = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.history_list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=0)

        self.history_data = []

        # ====================
        # MAIN DASHBOARD
        # ====================
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        
        # Split main frame into 2 equal columns:
        # Col 0: Input form
        # Col 1: Diagnosis & recommendation results
        self.main_frame.grid_columnconfigure(0, weight=1, minsize=450)
        self.main_frame.grid_columnconfigure(1, weight=1, minsize=500)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # --------------------
        # LEFT COLUMN (Form)
        # --------------------
        self.left_column = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.left_column.grid(row=0, column=0, sticky="nsew", padx=(10, 10), pady=10)
        self.left_column.grid_columnconfigure(0, weight=1)
        self.left_column.grid_rowconfigure(2, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(self.left_column, text="Evaluator Kualitas Tidur", font=ctk.CTkFont(size=22, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=10, pady=(15, 2))
        
        self.desc_label = ctk.CTkLabel(self.left_column, text="Sistem Hybrid: Certainty Factor + Random Forest", font=ctk.CTkFont(size=13), text_color="gray")
        self.desc_label.grid(row=1, column=0, padx=10, pady=(0, 10))

        # Input Form (Scrollable)
        self.input_frame = ctk.CTkScrollableFrame(self.left_column)
        self.input_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Form fields directly inside self.input_frame
        self.name_entry = self.create_entry(self.input_frame, 0, "Nama:")
        self.gender_var = ctk.StringVar(value="Laki-laki")
        self.create_dropdown(self.input_frame, 1, "Jenis Kelamin:", list(self.gender_map.keys()), self.gender_var)
        self.age_entry = self.create_entry(self.input_frame, 2, "Usia:")
        self.occupation_var = ctk.StringVar(value="Pelajar/Mahasiswa")
        self.create_dropdown(self.input_frame, 3, "Pekerjaan:", list(self.occupation_map.keys()), self.occupation_var)
        self.sleep_duration_entry = self.create_entry(self.input_frame, 4, "Durasi Tidur (jam):")
        self.stress_level_slider = self.create_slider(self.input_frame, 5, "Tingkat Stres (1-10):", 1, 10)
        self.physical_activity_entry = self.create_entry(self.input_frame, 6, "Aktivitas Fisik (menit/hari):")
        self.bmi_var = ctk.StringVar(value="Normal")
        self.create_dropdown(self.input_frame, 7, "Kategori BMI:", list(self.bmi_map.keys()), self.bmi_var)
        self.heart_rate_entry = self.create_entry(self.input_frame, 8, "Detak Jantung (bpm):")
        self.sleep_disorder_var = ctk.StringVar(value="Tidak Ada")
        self.create_dropdown(self.input_frame, 9, "Gangguan Tidur:", list(self.sleep_disorder_map.keys()), self.sleep_disorder_var)
        self.blood_pressure_var = ctk.StringVar(value="Normal")
        self.create_dropdown(self.input_frame, 10, "Tekanan Darah:", list(self.blood_pressure_map.keys()), self.blood_pressure_var)
        self.daily_steps_entry = self.create_entry(self.input_frame, 11, "Jumlah Langkah Harian:")

        self.predict_button = ctk.CTkButton(self.left_column, text="Evaluasi", command=self.submit_prediction, height=45, font=ctk.CTkFont(size=16, weight="bold"))
        self.predict_button.grid(row=3, column=0, pady=10, padx=10, sticky="ew")

        # --------------------
        # RIGHT COLUMN (Dashboard Results)
        # --------------------
        self.right_column = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.right_column.grid(row=0, column=1, sticky="nsew", padx=(10, 15), pady=10)
        self.right_column.grid_columnconfigure(0, weight=1)
        self.right_column.grid_rowconfigure(2, weight=0)
        self.right_column.grid_rowconfigure(3, weight=1)
        self.right_column.grid_rowconfigure(4, weight=0)

        # Title
        self.dashboard_title = ctk.CTkLabel(self.right_column, text="Dashboard Hasil & Rekomendasi", font=ctk.CTkFont(size=22, weight="bold"))
        self.dashboard_title.grid(row=0, column=0, padx=10, pady=(15, 10))

        # 1. Final Status Card (Displays result class BAIK, CUKUP, BURUK beautifully)
        self.status_card = ctk.CTkFrame(self.right_column, fg_color="#1a1a1a", border_width=2, border_color="#333333")
        self.status_card.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.status_card.grid_columnconfigure(0, weight=1)
        
        self.status_title_label = ctk.CTkLabel(self.status_card, text="KUALITAS TIDUR AKHIR", font=ctk.CTkFont(size=11, weight="bold"), text_color="#888888")
        self.status_title_label.grid(row=0, column=0, pady=(12, 0))
        
        self.final_status_label = ctk.CTkLabel(self.status_card, text="BELUM DIEVALUASI", font=ctk.CTkFont(size=30, weight="bold"), text_color="#555555")
        self.final_status_label.grid(row=1, column=0, pady=(2, 12))

        # 2. Score Dashboard Frame (Visual Hybrid Combined Scores + Recommendations)
        self.scores_frame = ctk.CTkFrame(self.right_column)
        self.scores_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.scores_frame.grid_columnconfigure(1, weight=1)
        self.scores_frame.grid_rowconfigure(4, weight=1)
        
        self.scores_title = ctk.CTkLabel(self.scores_frame, text="Bobot Skor Akhir (Formula Hybrid)", font=ctk.CTkFont(size=14, weight="bold"))
        self.scores_title.grid(row=0, column=0, columnspan=3, padx=15, pady=(12, 5), sticky="w")

        # Progress bar: BAIK
        self.lbl_baik_title = ctk.CTkLabel(self.scores_frame, text="BAIK", font=ctk.CTkFont(weight="bold"))
        self.lbl_baik_title.grid(row=1, column=0, padx=15, pady=6, sticky="w")
        self.pb_combined_baik = ctk.CTkProgressBar(self.scores_frame, progress_color="#2ecc71", height=12)
        self.pb_combined_baik.grid(row=1, column=1, padx=10, pady=6, sticky="ew")
        self.pb_combined_baik.set(0)
        self.lbl_combined_baik_val = ctk.CTkLabel(self.scores_frame, text="0.000 (0.0%)", font=ctk.CTkFont(size=12))
        self.lbl_combined_baik_val.grid(row=1, column=2, padx=15, pady=6, sticky="e")

        # Progress bar: CUKUP
        self.lbl_cukup_title = ctk.CTkLabel(self.scores_frame, text="CUKUP", font=ctk.CTkFont(weight="bold"))
        self.lbl_cukup_title.grid(row=2, column=0, padx=15, pady=6, sticky="w")
        self.pb_combined_cukup = ctk.CTkProgressBar(self.scores_frame, progress_color="#f1c40f", height=12)
        self.pb_combined_cukup.grid(row=2, column=1, padx=10, pady=6, sticky="ew")
        self.pb_combined_cukup.set(0)
        self.lbl_combined_cukup_val = ctk.CTkLabel(self.scores_frame, text="0.000 (0.0%)", font=ctk.CTkFont(size=12))
        self.lbl_combined_cukup_val.grid(row=2, column=2, padx=15, pady=6, sticky="e")

        # Progress bar: BURUK
        self.lbl_buruk_title = ctk.CTkLabel(self.scores_frame, text="BURUK", font=ctk.CTkFont(weight="bold"))
        self.lbl_buruk_title.grid(row=3, column=0, padx=15, pady=6, sticky="w")
        self.pb_combined_buruk = ctk.CTkProgressBar(self.scores_frame, progress_color="#e74c3c", height=12)
        self.pb_combined_buruk.grid(row=3, column=1, padx=10, pady=6, sticky="ew")
        self.pb_combined_buruk.set(0)
        self.lbl_combined_buruk_val = ctk.CTkLabel(self.scores_frame, text="0.000 (0.0%)", font=ctk.CTkFont(size=12))
        self.lbl_combined_buruk_val.grid(row=3, column=2, padx=15, pady=6, sticky="e")

        # Recommendation textbox inside scores_frame
        self.reco_frame = ctk.CTkFrame(self.scores_frame, fg_color="transparent")
        self.reco_frame.grid(row=4, column=0, columnspan=3, padx=15, pady=(10, 12), sticky="nsew")
        self.reco_frame.grid_columnconfigure(0, weight=1)
        self.reco_frame.grid_rowconfigure(1, weight=1)
        
        self.reco_title = ctk.CTkLabel(self.reco_frame, text="Saran / Rekomendasi Klinis:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#2196F3")
        self.reco_title.grid(row=0, column=0, sticky="w", pady=(0, 2))
        
        self.reco_text = ctk.CTkTextbox(self.reco_frame, height=75, wrap="word", font=ctk.CTkFont(size=12))
        self.reco_text.grid(row=1, column=0, sticky="nsew")
        self.reco_text.insert("0.0", "Harap lengkapi formulir masukan di sebelah kiri, lalu tekan tombol 'Evaluasi' untuk menampilkan hasil analisis hibrida beserta saran rekomendasi kesehatan.")
        self.reco_text.configure(state="disabled")

        # 3. Details Container (Displays CF and RF directly side-by-side)
        self.details_container = ctk.CTkFrame(self.right_column, fg_color="transparent")
        self.details_container.grid(row=3, column=0, padx=10, pady=(5, 5), sticky="nsew")
        self.details_container.grid_columnconfigure(0, weight=1, minsize=230)
        self.details_container.grid_columnconfigure(1, weight=1, minsize=230)
        self.details_container.grid_rowconfigure(0, weight=1)

        # --- Left Side: Certainty Factor (CF) ---
        self.cf_details_frame = ctk.CTkFrame(self.details_container)
        self.cf_details_frame.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="nsew")
        self.cf_details_frame.grid_columnconfigure(0, weight=1)
        self.cf_details_frame.grid_rowconfigure(2, weight=1)

        self.lbl_cf_title = ctk.CTkLabel(self.cf_details_frame, text="Certainty Factor (CF) Engine", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2196F3")
        self.lbl_cf_title.grid(row=0, column=0, padx=10, pady=(8, 2), sticky="w")

        self.lbl_cf_summary = ctk.CTkLabel(self.cf_details_frame, text="Keputusan CF: - (CF value: 0.000)", font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_cf_summary.grid(row=1, column=0, padx=10, pady=2, sticky="w")
        
        self.cf_rules_text = ctk.CTkTextbox(self.cf_details_frame, wrap="word", height=90, font=ctk.CTkFont(size=11))
        self.cf_rules_text.grid(row=2, column=0, padx=10, pady=(2, 8), sticky="nsew")
        self.cf_rules_text.insert("0.0", "Aturan terpicu (Fired Rules) pakar akan dimunculkan di sini...")
        self.cf_rules_text.configure(state="disabled")

        # --- Right Side: Random Forest (RF) ---
        self.rf_details_frame = ctk.CTkFrame(self.details_container)
        self.rf_details_frame.grid(row=0, column=1, padx=(5, 0), pady=0, sticky="nsew")
        self.rf_details_frame.grid_columnconfigure(1, weight=1)

        self.lbl_rf_title = ctk.CTkLabel(self.rf_details_frame, text="Random Forest (RF) Model", font=ctk.CTkFont(size=12, weight="bold"), text_color="#2196F3")
        self.lbl_rf_title.grid(row=0, column=0, columnspan=3, padx=10, pady=(8, 2), sticky="w")

        self.lbl_rf_summary = ctk.CTkLabel(self.rf_details_frame, text="Prediksi RF: -", font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_rf_summary.grid(row=1, column=0, columnspan=3, padx=10, pady=2, sticky="w")
        
        # RF Prob: BAIK
        self.lbl_rf_baik = ctk.CTkLabel(self.rf_details_frame, text="BAIK:", font=ctk.CTkFont(size=11))
        self.lbl_rf_baik.grid(row=2, column=0, padx=10, pady=1, sticky="w")
        self.pb_rf_baik = ctk.CTkProgressBar(self.rf_details_frame, progress_color="#2ecc71", height=8)
        self.pb_rf_baik.grid(row=2, column=1, padx=5, pady=1, sticky="ew")
        self.pb_rf_baik.set(0)
        self.lbl_rf_baik_val = ctk.CTkLabel(self.rf_details_frame, text="0%", font=ctk.CTkFont(size=11))
        self.lbl_rf_baik_val.grid(row=2, column=2, padx=10, pady=1, sticky="e")

        # RF Prob: CUKUP
        self.lbl_rf_cukup = ctk.CTkLabel(self.rf_details_frame, text="CUKUP:", font=ctk.CTkFont(size=11))
        self.lbl_rf_cukup.grid(row=3, column=0, padx=10, pady=1, sticky="w")
        self.pb_rf_cukup = ctk.CTkProgressBar(self.rf_details_frame, progress_color="#f1c40f", height=8)
        self.pb_rf_cukup.grid(row=3, column=1, padx=5, pady=1, sticky="ew")
        self.pb_rf_cukup.set(0)
        self.lbl_rf_cukup_val = ctk.CTkLabel(self.rf_details_frame, text="0%", font=ctk.CTkFont(size=11))
        self.lbl_rf_cukup_val.grid(row=3, column=2, padx=10, pady=1, sticky="e")

        # RF Prob: BURUK
        self.lbl_rf_buruk = ctk.CTkLabel(self.rf_details_frame, text="BURUK:", font=ctk.CTkFont(size=11))
        self.lbl_rf_buruk.grid(row=4, column=0, padx=10, pady=1, sticky="w")
        self.pb_rf_buruk = ctk.CTkProgressBar(self.rf_details_frame, progress_color="#e74c3c", height=8)
        self.pb_rf_buruk.grid(row=4, column=1, padx=5, pady=1, sticky="ew")
        self.pb_rf_buruk.set(0)
        self.lbl_rf_buruk_val = ctk.CTkLabel(self.rf_details_frame, text="0%", font=ctk.CTkFont(size=11))
        self.lbl_rf_buruk_val.grid(row=4, column=2, padx=10, pady=1, sticky="e")

        # 4. Formula Explanation Card
        self.formula_frame = ctk.CTkFrame(self.right_column, fg_color="#1d1d1d", border_width=1, border_color="#333333")
        self.formula_frame.grid(row=4, column=0, padx=10, pady=(5, 10), sticky="ew")
        self.formula_frame.grid_columnconfigure(0, weight=1)
        
        formula_text = (
            "Keterangan Formula Hybrid:\n"
            "Skor Akhir = (0.4 * CF_score) + (0.6 * RF_probability)\n"
            "Keputusan final diambil dari kelas dengan Skor Akhir tertinggi."
        )
        self.lbl_formula_desc = ctk.CTkLabel(
            self.formula_frame, 
            text=formula_text, 
            font=ctk.CTkFont(size=11, slant="italic"), 
            justify="center",
            text_color="#888888"
        )
        self.lbl_formula_desc.grid(row=0, column=0, padx=10, pady=10)

        self.load_history()

    def create_entry(self, parent, row, label_text):
        label = ctk.CTkLabel(parent, text=label_text)
        label.grid(row=row, column=0, padx=10, pady=8, sticky="w")
        entry = ctk.CTkEntry(parent)
        entry.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        return entry

    def create_dropdown(self, parent, row, label_text, values, variable):
        label = ctk.CTkLabel(parent, text=label_text)
        label.grid(row=row, column=0, padx=10, pady=8, sticky="w")
        menu = ctk.CTkOptionMenu(parent, values=values, variable=variable)
        menu.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        return menu

    def create_slider(self, parent, row, label_text, min_val, max_val):
        label = ctk.CTkLabel(parent, text=label_text)
        label.grid(row=row, column=0, padx=10, pady=8, sticky="w")
        slider_var = ctk.IntVar(value=5)
        slider = ctk.CTkSlider(parent, from_=min_val, to=max_val, number_of_steps=9, variable=slider_var)
        slider.grid(row=row, column=1, padx=10, pady=8, sticky="ew")
        val_label = ctk.CTkLabel(parent, textvariable=slider_var)
        val_label.grid(row=row, column=2, padx=10, pady=8)
        return slider_var

    def new_evaluation(self):
        # Exit preview mode
        self.is_preview_mode = False
        self.current_consultation_id = None

        # Reset form
        self.name_entry.delete(0, 'end')
        self.gender_var.set("Laki-laki")
        self.age_entry.delete(0, 'end')
        self.occupation_var.set("Pelajar/Mahasiswa")
        self.sleep_duration_entry.delete(0, 'end')
        self.stress_level_slider.set(5)
        self.physical_activity_entry.delete(0, 'end')
        self.bmi_var.set("Normal")
        self.heart_rate_entry.delete(0, 'end')
        self.sleep_disorder_var.set("Tidak Ada")
        self.blood_pressure_var.set("Normal")
        self.daily_steps_entry.delete(0, 'end')

        # Reset dashboard elements to default
        self.final_status_label.configure(text="BELUM DIEVALUASI", text_color="#555555")
        self.status_card.configure(border_color="#333333")
        
        self.pb_combined_baik.set(0)
        self.pb_combined_cukup.set(0)
        self.pb_combined_buruk.set(0)
        self.lbl_combined_baik_val.configure(text="0.000 (0.0%)")
        self.lbl_combined_cukup_val.configure(text="0.000 (0.0%)")
        self.lbl_combined_buruk_val.configure(text="0.000 (0.0%)")

        self.reco_text.configure(state="normal")
        self.reco_text.delete("0.0", "end")
        self.reco_text.insert("0.0", "Harap lengkapi formulir masukan di sebelah kiri, lalu tekan tombol 'Evaluasi' untuk menampilkan hasil analisis hibrida beserta saran rekomendasi kesehatan.")
        self.reco_text.configure(state="disabled")

        self.lbl_cf_summary.configure(text="Keputusan CF: - (CF value: 0.000)")
        self.cf_rules_text.configure(state="normal")
        self.cf_rules_text.delete("0.0", "end")
        self.cf_rules_text.insert("0.0", "Aturan terpicu (Fired Rules) pakar akan dimunculkan di sini...")
        self.cf_rules_text.configure(state="disabled")

        self.lbl_rf_summary.configure(text="Prediksi RF: -")
        self.pb_rf_baik.set(0)
        self.pb_rf_cukup.set(0)
        self.pb_rf_buruk.set(0)
        self.lbl_rf_baik_val.configure(text="0%")
        self.lbl_rf_cukup_val.configure(text="0%")
        self.lbl_rf_buruk_val.configure(text="0%")

        # Enable evaluate button
        self.predict_button.configure(state="normal")
        self.predict_button.configure(text="Evaluasi")

    def submit_prediction(self):
        if self.is_preview_mode:
            return  # Prevent submission if in preview mode

        # Validate that no entry is empty
        name = self.name_entry.get().strip()
        age = self.age_entry.get().strip()
        duration = self.sleep_duration_entry.get().strip()
        activity = self.physical_activity_entry.get().strip()
        hr = self.heart_rate_entry.get().strip()
        steps = self.daily_steps_entry.get().strip()

        if not all([name, age, duration, activity, hr, steps]):
            messagebox.showwarning("Input Tidak Lengkap", "Harap isi semua kolom input sebelum melakukan evaluasi.")
            return

        try:
            payload = {
                "features": {
                    "name": name,
                    "gender": self.gender_map.get(self.gender_var.get(), "Male"),
                    "age": int(age),
                    "occupation": self.occupation_map.get(self.occupation_var.get(), "Student"),
                    "sleep_duration": float(duration),
                    "stress_level": self.stress_level_slider.get(),
                    "physical_activity": int(activity),
                    "bmi_category": self.bmi_map.get(self.bmi_var.get(), "Normal Weight"),
                    "heart_rate": int(hr),
                    "sleep_disorder": self.sleep_disorder_map.get(self.sleep_disorder_var.get(), "None"),
                    "blood_pressure": self.blood_pressure_map.get(self.blood_pressure_var.get(), "Normal"),
                    "daily_steps": int(steps)
                }
            }
            
            response = requests.post("http://127.0.0.1:5000/predict", json=payload)
            if response.status_code == 200:
                data = response.json()
                self.display_result(data)
                self.load_history() # Refresh history
                
                self.is_preview_mode = True
                self.current_consultation_id = data.get("consultation_id")
                self.predict_button.configure(state="disabled")
                self.predict_button.configure(text="Hasil Evaluasi")

            else:
                messagebox.showerror("Error API", f"Gagal mendapatkan prediksi: {response.text}")
                
        except ValueError:
            messagebox.showerror("Input Error", "Harap pastikan semua input numerik berisi angka yang valid.")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Connection Error", "Tidak dapat terhubung ke server Flask. Pastikan app.py berjalan di port 5000.")

    def generate_report_text(self, data, is_preview=False):
        final_pred = data.get('final_prediction') or data.get('final_class', 'N/A')
        
        if is_preview:
            output = f"=== Hasil Evaluasi ===\n"
        else:
            output = f"=== HASIL Evaluasi ===\n"
            
        output += f"HASIL AKHIR SLEEP QUALITY: {final_pred}\n\n"
        
        cf_res = data.get('cf_result', {})
        rf_res = data.get('rf_result', {})
        
        output += f"--- Certainty Factor (CF) Engine ---\n"
        output += f"CF Class: {cf_res.get('class', 'N/A')} (Score: {cf_res.get('cf_value', 0):.3f})\n"
        cf_all = cf_res.get('all_scores', {})
        output += f"Skor Kelas CF: BAIK: {cf_all.get('BAIK',0):.3f}, CUKUP: {cf_all.get('CUKUP',0):.3f}, BURUK: {cf_all.get('BURUK',0):.3f}\n"
        output += "Fired Rules:\n"
        for r in cf_res.get('fired_rules', []):
            output += f" - [{r['id']}] {r['desc']} (CF added: {r['cf_added']})\n"
            
        output += f"\n--- Random Forest (RF) Model ---\n"
        output += f"Prediksi RF: {rf_res.get('prediction', 'N/A')}\n"
        probs = rf_res.get('probabilities', {})
        output += f"Probabilitas: BAIK: {probs.get('BAIK',0):.2f}, CUKUP: {probs.get('CUKUP',0):.2f}, BURUK: {probs.get('BURUK',0):.2f}\n"
        
        combined = data.get('combined_scores', {})
        output += f"\n--- Perhitungan Akhir Mesin Hybrid ---\n"
        output += f"Skor Gabungan (BAIK): {combined.get('BAIK', 0):.3f}\n"
        output += f"Skor Gabungan (CUKUP): {combined.get('CUKUP', 0):.3f}\n"
        output += f"Skor Gabungan (BURUK): {combined.get('BURUK', 0):.3f}\n"
        output += f"Formula: Skor Akhir = (0.4 * CF) + (0.6 * RF)\n"
        
        return output

    def display_result(self, data, is_preview=False):
        final_pred = data.get('final_prediction') or data.get('final_class', 'N/A')
        
        # 1. Update Final Status Card color & text
        if final_pred == "BAIK":
            self.final_status_label.configure(text="BAIK (GOOD)", text_color="#2ecc71")
            self.status_card.configure(border_color="#2ecc71")
            reco_msg = "Kualitas tidur Anda tergolong BAIK. Pertahankan gaya hidup sehat Anda dengan tidur yang teratur antara 7-9 jam per hari, melakukan aktivitas fisik minimal 30 menit, dan menjaga pikiran tetap rileks sebelum tidur."
        elif final_pred == "CUKUP":
            self.final_status_label.configure(text="CUKUP (NORMAL)", text_color="#f1c40f")
            self.status_card.configure(border_color="#f1c40f")
            reco_msg = "Kualitas tidur Anda CUKUP. Cobalah untuk menyisihkan waktu tidur yang konsisten, membatasi konsumsi kafein atau penggunaan gadget minimal 1 jam sebelum tidur, serta kelola tingkat stres harian Anda agar tidur lebih berkualitas."
        elif final_pred == "BURUK":
            self.final_status_label.configure(text="BURUK (POOR)", text_color="#e74c3c")
            self.status_card.configure(border_color="#e74c3c")
            reco_msg = "Kualitas tidur Anda BURUK. Anda sangat disarankan untuk merancang jadwal tidur yang disiplin, meminimalkan layar gadget di kamar, melakukan teknik relaksasi pernapasan untuk menurunkan stres, serta segera berkonsultasi dengan dokter apabila keluhan insomnia atau gangguan pernapasan terus berlanjut."
        else:
            self.final_status_label.configure(text=final_pred, text_color="white")
            self.status_card.configure(border_color="#333333")
            reco_msg = f"Hasil klasifikasi tidak terdefinisi ({final_pred})."

        # 2. Update Recommendation
        self.reco_text.configure(state="normal")
        self.reco_text.delete("0.0", "end")
        self.reco_text.insert("0.0", reco_msg)
        self.reco_text.configure(state="disabled")

        # 3. Update Combined Score progress bars & text
        combined = data.get('combined_scores', {})
        score_baik = combined.get('BAIK', 0.0)
        score_cukup = combined.get('CUKUP', 0.0)
        score_buruk = combined.get('BURUK', 0.0)

        self.pb_combined_baik.set(score_baik)
        self.pb_combined_cukup.set(score_cukup)
        self.pb_combined_buruk.set(score_buruk)

        self.lbl_combined_baik_val.configure(text=f"{score_baik:.3f} ({score_baik*100:.1f}%)")
        self.lbl_combined_cukup_val.configure(text=f"{score_cukup:.3f} ({score_cukup*100:.1f}%)")
        self.lbl_combined_buruk_val.configure(text=f"{score_buruk:.3f} ({score_buruk*100:.1f}%)")

        # 4. Update Certainty Factor Details Tab
        cf_res = data.get('cf_result', {})
        cf_class = cf_res.get('class', 'N/A')
        cf_val = cf_res.get('cf_value', 0.0)
        self.lbl_cf_summary.configure(text=f"Keputusan CF: {cf_class} (CF value: {cf_val:.3f})")
        
        fired = cf_res.get('fired_rules', [])
        rules_output = ""
        if fired:
            for r in fired:
                rules_output += f"• [{r['id']}] {r['desc']} (CF: +{r['cf_added']})\n"
        else:
            rules_output = "Tidak ada aturan pakar (rules) Certainty Factor yang terpicu untuk input saat ini."

        self.cf_rules_text.configure(state="normal")
        self.cf_rules_text.delete("0.0", "end")
        self.cf_rules_text.insert("0.0", rules_output)
        self.cf_rules_text.configure(state="disabled")

        # 5. Update Random Forest Details Tab
        rf_res = data.get('rf_result', {})
        rf_class = rf_res.get('prediction', 'N/A')
        probs = rf_res.get('probabilities', {})
        p_baik = probs.get('BAIK', 0.0)
        p_cukup = probs.get('CUKUP', 0.0)
        p_buruk = probs.get('BURUK', 0.0)

        max_prob = max(p_baik, p_cukup, p_buruk)
        self.lbl_rf_summary.configure(text=f"Prediksi RF: {rf_class} (Keyakinan: {max_prob*100:.1f}%)")
        
        self.pb_rf_baik.set(p_baik)
        self.pb_rf_cukup.set(p_cukup)
        self.pb_rf_buruk.set(p_buruk)

        self.lbl_rf_baik_val.configure(text=f"{p_baik*100:.0f}%")
        self.lbl_rf_cukup_val.configure(text=f"{p_cukup*100:.0f}%")
        self.lbl_rf_buruk_val.configure(text=f"{p_buruk*100:.0f}%")

    def load_history(self):
        try:
            response = requests.get("http://127.0.0.1:5000/history")
            if response.status_code == 200:
                self.history_data = response.json()
                self.render_history()
        except requests.exceptions.ConnectionError:
            pass # Backend might not be running yet

    def render_history(self):
        # Clear existing
        for widget in self.history_list_frame.winfo_children():
            widget.destroy()

        if not self.history_data:
            lbl = ctk.CTkLabel(self.history_list_frame, text="Riwayat tidak tersedia.", text_color="gray")
            lbl.pack(pady=20)
            return

        for item in self.history_data:
            item_frame = ctk.CTkFrame(self.history_list_frame, fg_color="#2b2b2b")
            item_frame.pack(fill="x", padx=2, pady=2)
            item_frame.grid_columnconfigure(0, weight=1)

            text = f"{item['name']} - {item['final_class']}\n{item['date']}"
            btn = ctk.CTkButton(item_frame, text=text, anchor="w", fg_color="transparent", hover_color="#3b3b3b",
                                font=ctk.CTkFont(size=12),
                                command=lambda d=item: self.preview_history(d))
            btn.grid(row=0, column=0, sticky="ew", padx=(5, 2), pady=2)

            # Export button (⭳)
            export_btn = ctk.CTkButton(item_frame, text="⭳", width=24, height=24,
                                       command=lambda d=item: self.export_csv(d))
            export_btn.grid(row=0, column=1, padx=(1, 1), pady=2)

            # Delete button (🗑)
            del_btn = ctk.CTkButton(item_frame, text="🗑", width=24, height=24, fg_color="#b22222", hover_color="#8b0000",
                                    command=lambda d=item: self.delete_history(d))
            del_btn.grid(row=0, column=2, padx=(2, 5), pady=2)

    def preview_history(self, data):
        self.is_preview_mode = True
        self.current_consultation_id = data.get("consultation_id")

        # Disable Predict button
        self.predict_button.configure(state="disabled")
        self.predict_button.configure(text="Evaluasi")

        # Populate fields
        self.name_entry.delete(0, 'end')
        self.name_entry.insert(0, data.get('name', ''))
        
        self.gender_var.set(self.inv_gender_map.get(data.get('gender', 'Male'), 'Laki-laki'))
        
        self.age_entry.delete(0, 'end')
        self.age_entry.insert(0, str(data.get('age', '')))
        
        self.occupation_var.set(self.inv_occupation_map.get(data.get('occupation', 'Student'), 'Pelajar/Mahasiswa'))
        
        self.sleep_duration_entry.delete(0, 'end')
        self.sleep_duration_entry.insert(0, str(data.get('sleep_duration', '')))
        
        self.stress_level_slider.set(data.get('stress_level', 5))
        
        self.physical_activity_entry.delete(0, 'end')
        self.physical_activity_entry.insert(0, str(data.get('physical_activity', '')))
        
        self.bmi_var.set(self.inv_bmi_map.get(data.get('bmi_category', 'Normal Weight'), 'Normal'))
        
        self.heart_rate_entry.delete(0, 'end')
        self.heart_rate_entry.insert(0, str(data.get('heart_rate', '')))
        
        self.sleep_disorder_var.set(self.inv_sleep_disorder_map.get(data.get('sleep_disorder', 'None'), 'Tidak Ada'))
        self.blood_pressure_var.set(self.inv_blood_pressure_map.get(data.get('blood_pressure', 'Normal'), 'Normal'))
        
        self.daily_steps_entry.delete(0, 'end')
        self.daily_steps_entry.insert(0, str(data.get('daily_steps', '')))
        
        # Populate Dashboard widgets
        self.display_result(data, is_preview=True)

    def delete_history(self, data):
        if messagebox.askyesno("Konfirmasi Hapus", f"Apakah Anda yakin ingin menghapus evaluasi ini?\n{data['name']} - {data['date']}"):
            try:
                response = requests.delete(f"http://127.0.0.1:5000/history/{data['consultation_id']}")
                if response.status_code == 200:
                    self.load_history()
                    # If deleting the currently previewed item, clear the form
                    if self.current_consultation_id == data['consultation_id']:
                        self.new_evaluation()
                else:
                    messagebox.showerror("Error", f"Gagal menghapus: {response.text}")
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))

    def export_csv(self, data):
        import re
        
        raw_date = data.get('date', '')
        # Replace spaces, colons, slashes with underscores for a safe filename
        safe_date = re.sub(r'[^\w\-_]', '_', raw_date)
        
        name = data.get('name', 'Anonymous').replace(" ", "_")
        result = data.get('final_class', 'Result').replace(" ", "")
        
        default_filename = f"{name}_{result}_{safe_date}.csv"

        file_path = filedialog.asksaveasfilename(
            initialfile=default_filename,
            defaultextension=".csv",
            filetypes=[("File CSV", "*.csv"), ("Semua file", "*.*")],
            title="Simpan Riwayat sebagai CSV"
        )
        
        if file_path:
            try:
                row_copy = data.copy()
                row_copy['Laporan_Detail'] = self.generate_report_text(data, is_preview=True)
                
                # Convert complex dicts to JSON strings for CSV
                if 'cf_result' in row_copy:
                    row_copy['cf_result'] = json.dumps(row_copy['cf_result'])
                if 'rf_result' in row_copy:
                    row_copy['rf_result'] = json.dumps(row_copy['rf_result'])
                if 'combined_scores' in row_copy:
                    row_copy['combined_scores'] = json.dumps(row_copy['combined_scores'])
                if 'fired_rules' in row_copy:
                    row_copy['fired_rules'] = json.dumps(row_copy['fired_rules'])

                keys = row_copy.keys()
                with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    writer.writeheader()
                    writer.writerow(row_copy)
                messagebox.showinfo("Sukses", f"Berhasil mengekspor riwayat ke:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error Ekspor", f"Gagal menulis CSV: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
