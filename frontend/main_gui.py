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

        self.title("Sisru: Sistem Pakar Evaluasi Kualitas Tidur")
        self.geometry("1000x800")
        
        # Grid config:
        # Col 0: Sidebar (Weight 0, minsize=300)
        # Col 1: Main Content (Weight 1)
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
        # MAIN CONTENT
        # ====================
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(self.main_frame, text="Evaluator Kualitas Tidur", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.desc_label = ctk.CTkLabel(self.main_frame, text="Sistem Hybrid: Certainty Factor + Random Forest", font=ctk.CTkFont(size=14))
        self.desc_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Input Form
        self.input_frame = ctk.CTkScrollableFrame(self.main_frame)
        self.input_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        # Form fields
        self.name_entry = self.create_entry(0, "Nama:")
        self.gender_var = ctk.StringVar(value="Laki-laki")
        self.create_dropdown(1, "Jenis Kelamin:", list(self.gender_map.keys()), self.gender_var)
        self.age_entry = self.create_entry(2, "Usia:")
        self.occupation_var = ctk.StringVar(value="Pelajar/Mahasiswa")
        self.create_dropdown(3, "Pekerjaan:", list(self.occupation_map.keys()), self.occupation_var)
        self.sleep_duration_entry = self.create_entry(4, "Durasi Tidur (jam):")
        self.stress_level_slider = self.create_slider(5, "Tingkat Stres (1-10):", 1, 10)
        self.physical_activity_entry = self.create_entry(6, "Aktivitas Fisik (menit/hari):")
        self.bmi_var = ctk.StringVar(value="Normal")
        self.create_dropdown(7, "Kategori BMI:", list(self.bmi_map.keys()), self.bmi_var)
        self.heart_rate_entry = self.create_entry(8, "Detak Jantung (bpm):")
        self.sleep_disorder_var = ctk.StringVar(value="Tidak Ada")
        self.create_dropdown(9, "Gangguan Tidur:", list(self.sleep_disorder_map.keys()), self.sleep_disorder_var)
        self.blood_pressure_var = ctk.StringVar(value="Normal")
        self.create_dropdown(10, "Tekanan Darah:", list(self.blood_pressure_map.keys()), self.blood_pressure_var)
        self.daily_steps_entry = self.create_entry(11, "Jumlah Langkah Harian:")

        self.predict_button = ctk.CTkButton(self.main_frame, text="Evaluasi", command=self.submit_prediction, height=40, font=ctk.CTkFont(size=16, weight="bold"))
        self.predict_button.grid(row=3, column=0, pady=10)

        # Result Textbox
        self.result_textbox = ctk.CTkTextbox(self.main_frame, height=200)
        self.result_textbox.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.result_textbox.insert("0.0", "Hasil akan ditampilkan di sini...\n")
        self.result_textbox.configure(state="disabled")
        
        self.load_history()

    def create_entry(self, row, label_text):
        label = ctk.CTkLabel(self.input_frame, text=label_text)
        label.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        entry = ctk.CTkEntry(self.input_frame)
        entry.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        return entry

    def create_dropdown(self, row, label_text, values, variable):
        label = ctk.CTkLabel(self.input_frame, text=label_text)
        label.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        menu = ctk.CTkOptionMenu(self.input_frame, values=values, variable=variable)
        menu.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        return menu

    def create_slider(self, row, label_text, min_val, max_val):
        label = ctk.CTkLabel(self.input_frame, text=label_text)
        label.grid(row=row, column=0, padx=10, pady=10, sticky="w")
        slider_var = ctk.IntVar(value=5)
        slider = ctk.CTkSlider(self.input_frame, from_=min_val, to=max_val, number_of_steps=9, variable=slider_var)
        slider.grid(row=row, column=1, padx=10, pady=10, sticky="ew")
        val_label = ctk.CTkLabel(self.input_frame, textvariable=slider_var)
        val_label.grid(row=row, column=2, padx=10, pady=10)
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

        # Reset result box
        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("0.0", "end")
        self.result_textbox.insert("0.0", "Hasil akan ditampilkan di sini...\n")
        self.result_textbox.configure(state="disabled")

        # Enable evaluate button
        self.predict_button.configure(state="normal")
        self.predict_button.configure(text="Evaluasi")

    def submit_prediction(self):
        if self.is_preview_mode:
            return  # Prevent submission if somehow button is clicked in preview mode

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
                
                # We optionally enter preview mode of this new evaluation, or leave it as new.
                # Since user just ran it, they shouldn't run identical easily, so let's set it as preview mode.
                self.is_preview_mode = True
                self.current_consultation_id = data.get("consultation_id")
                self.predict_button.configure(state="disabled")
                self.predict_button.configure(text="Hasil Evaluasi")

            else:
                messagebox.showerror("Error API", f"Gagal mendapatkan prediksi: {response.text}")
                
        except ValueError as e:
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
        self.result_textbox.configure(state="normal")
        self.result_textbox.delete("0.0", "end")
        output = self.generate_report_text(data, is_preview)
        self.result_textbox.insert("0.0", output)
        self.result_textbox.configure(state="disabled")

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
        
        # Populate Result Textbox
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
