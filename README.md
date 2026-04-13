# FOCUS: Facial Observation for Classroom Understanding and Surveillance

**FOCUS** is an AI-powered attendance and engagement tracking system designed for modern classrooms. It leverages cutting-edge computer vision to automate student identification and analyze real-time engagement levels through gaze tracking and pose estimation, while ensuring strict compliance with data privacy standards (DPDP 2023).

---

## Features

- **Automated Attendance**: High-accuracy face recognition using InsightFace (Buffalo_L).
- **Engagement Analytics**: Real-time gaze and head-pose analysis using MediaPipe FaceMesh.
- **Classroom Heatmap**: Zone-wise visualization of student activity and focus levels.
- **Incident Detection**: Automated phone detection using YOLOv8 to identify distractions.
- **Privacy First**: Secure biometric encryption and automated data deletion policies.
- **Reporting**: Professional PDF and Excel report generation with immutable audit logs.

---

## Technology Stack

- **Backend**: FastAPI (Python 3.12), SQLAlchemy (SQLite), Uvicorn.
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts.
- **Computer Vision**:
  - `InsightFace`: Robust face identification.
  - `MediaPipe`: Precise facial landmarking and gaze tracking.
  - `YOLOv8`: Object detection for distractions.

---

## Installation Guide

### Prerequisites
- Python 3.12+
- Node.js 18+
- Visual Studio C++ Build Tools (Required for InsightFace)

### 1. Backend Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/Samyak-777/F.O.C.U.S.git
   cd F.O.C.U.S.
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. **InsightFace Windows Note**: If the standard installation fails, install the provided wheel:
   ```bash
   pip install insightface-0.7.3-cp312-cp312-win_amd64.whl
   ```
5. Configure environment:
   ```bash
   cp .env.example .env
   # Update .env with your configuration (Camera Index, DB path, etc.)
   ```

### 2. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```

---

## Running the Project

1. **Start the Backend**:
   From the project root:
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`.

2. **Start the Frontend**:
   From the `frontend` directory:
   ```bash
   npm run dev
   ```
   The application will be available at `http://localhost:5173`.

---

## Privacy & Compliance (DPDP 2023)
FOCUS is built with the Digital Personal Data Protection Act (DPDP 2023) at its core:
- **No Raw Images**: The system never stores raw footage; only encrypted mathematical embeddings are persisted.
- **Consent Management**: Explicit student consent is required for biometric processing.
- **Data Deletion**: Biometric data is automatically purged within 24 hours of consent revocation.

---

## 🎓 Academic Info
Developed as part of **CSL308 SE Course Mini Project** at **VNIT Nagpur** (Group G14).
