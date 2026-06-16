# Sleep Quality Expert System

This is a Hybrid Expert System (Certainty Factor + Random Forest) built with Python, CustomTkinter (GUI), and a Flask API.

## Project Setup Guide

If you are setting this up on a fresh machine or pulling the code for the first time, you need to configure your Python environment. Python uses `pip` as its package manager to download the external libraries (like Flask, scikit-learn, etc.) that this project needs.

Follow these steps exactly to set up and run the project on Windows:

### Step 1: Create a Virtual Environment
A virtual environment isolates this project's packages from your global Python installation.
Open your terminal (PowerShell) inside the `sispak-turu` folder and run:
```powershell
python -m venv venv
```
*(This creates a folder named `venv` containing a fresh Python environment).*

### Step 2: Install Dependencies
You need to install the required libraries using the `requirements.txt` files. Run:
```powershell
.\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\venv\Scripts\python.exe -m pip install -r frontend\requirements.txt
```

### Step 3: Train the Machine Learning Model
Before starting the backend, you must train the Random Forest model using the provided dataset. Run:
```powershell
.\venv\Scripts\python.exe backend\train_model.py
```
*(This will read your dataset and generate `rf_model.pkl` inside the `backend` folder).*

### Step 4: Run the Application
You need **two** terminals running simultaneously: one for the Backend API and one for the GUI.

**Terminal 1 (Backend API):**
```powershell
cd backend
..\venv\Scripts\python.exe app.py
```
*(Leave this running. It hosts the Flask API on `http://127.0.0.1:5000`)*

**Terminal 2 (Desktop GUI):**
Open a new terminal window inside the `sispak-turu` folder and run:
```powershell
cd frontend
..\venv\Scripts\python.exe main_gui.py
```

