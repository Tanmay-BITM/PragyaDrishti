# PragyaDrishti REST API Documentation

Base URL: `http://localhost:8000/api/v1`

## Authentication (`/auth`)
- `POST /auth/register`: Register new user with email, password, full name, and role.
- `POST /auth/login`: Authenticate user and receive JWT access token.
- `POST /auth/google-login`: OAuth single sign-on helper.

## Datasets (`/datasets`)
- `POST /datasets/upload`: Upload CSV or Excel file.
- `GET /datasets/list`: List user datasets.
- `GET /datasets/{id}/preview`: Fetch dataset rows and schema metadata.
- `POST /datasets/{id}/auto-clean`: Execute automated data cleaning pipeline.

## Prompt-to-ML & Inference (`/prompt-ml`)
- `POST /prompt-ml/train`: Natural language prompt to AutoML model pipeline execution.
- `POST /prompt-ml/predict/{model_id}`: Real-time prediction REST endpoint.
- `GET /prompt-ml/download-model/{model_id}`: Download trained `.pkl` / `.joblib` model artifact.

## Analytics & Forecasting
- `POST /analytics/query/{dataset_id}`: Natural language query to chart spec.
- `GET /forecasting/{dataset_id}`: Time series forecast with upper/lower confidence bounds.

## Face Recognition & Student Portal (`/face-recognition`)
- `POST /face-recognition/recognize`: Upload photo for instant face matching and profile retrieval.

## Reports (`/reports`)
- `POST /reports/generate`: Generate PDF, Excel, PPTX, or HTML analytical report.
- `GET /reports/download/{report_id}`: Download generated report file.
