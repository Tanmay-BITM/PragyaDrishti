# PragyaDrishti: AI-Powered Data Visualization & Prompt-to-ML Assistant

PragyaDrishti is an enterprise SaaS platform that allows anyone to upload datasets and interact with them using natural language prompts. It automates dataset cleaning, AutoML model training, algorithm competition, feature importance extraction, multi-chart visualization, student face recognition, and multi-format report generation.

---

## 🌟 Key Features Across 16 Modules

1. **Modern Landing Page**: Glassmorphism design system, dark/light theme, pricing, and features.
2. **JWT & OAuth Authentication**: Password hashing, JWT tokens, RBAC roles (`ADMIN`, `ANALYST`, `STUDENT`).
3. **Dataset Ingestion**: CSV & Excel drag-and-drop upload with statistical schema inspector.
4. **Automated Data Cleaning**: Quality scoring (0-100%), missing value imputation, IQR outlier clipping, duplicate removal.
5. **Flagship Prompt-to-ML Engine**: Type prompts like *"Predict house prices"*, *"Forecast sales"*, *"Detect fraud"*. AI infers ML task, fits optimal model, exports `.pkl`, and deploys REST prediction endpoint.
6. **AutoML Benchmark**: Compares Random Forest, XGBoost, LightGBM, SVM, and PyTorch MLPs with cross-validation leaderboard.
7. **Natural Language Analytics**: Converts plain English queries into chart aggregations.
8. **13-Chart Visualization Studio**: Bar, Pie, Line, Scatter, Heatmap, Correlation Matrix, Radar, Box Plot, and Custom Drag-and-Drop Dashboard.
9. **AI Executive Insights**: Storytelling markdown cards, key trends, and anomaly detection.
10. **Predictive Forecasting**: Exponential smoothing & ML time series with lower/upper confidence bounds.
11. **Student Face Recognition**: OpenCV / DeepFace facial feature matching to student profiles, attendance, and GPA metrics.
12. **Personal Command Center**: Centralized workspace overview for datasets, models, reports, and alerts.
13. **Multi-Format Report Generator**: One-click download of PDF, Excel, PowerPoint, and HTML reports.
14. **System Admin Dashboard**: Telemetry monitoring for CPU, Memory, User catalog, and security logs.
15. **AI Chatbot Agent**: Dataset-aware conversational assistant powered by Gemini 1.5 with multi-step reasoning.
16. **Containerization & CI/CD**: Fully Dockerized with `docker-compose.yml` and GitHub Actions pipeline.

---

## 🚀 Quick Start Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Run Backend Server
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend Swagger API Documentation is available at: `http://localhost:8000/docs`

### 2. Run Frontend App
```bash
cd frontend
npm install
npm run dev
```
Frontend web app is available at: `http://localhost:3000`

### 3. Docker Compose Deployment
```bash
cd docker
docker-compose up --build
```
