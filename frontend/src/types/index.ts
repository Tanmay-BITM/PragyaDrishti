export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'ADMIN' | 'ANALYST' | 'STUDENT';
  api_key?: string;
}

export interface Dataset {
  id: number;
  name: string;
  filename: string;
  row_count: number;
  col_count: number;
  file_size_bytes: number;
  quality_score: number;
  columns_json?: string;
  summary_json?: string;
  version: number;
  created_at: string;
}

export interface MLModel {
  id: number;
  name: string;
  task_type: string;
  target_column?: string;
  best_algorithm: string;
  metrics_json?: string;
  feature_importance_json?: string;
  leaderboard_json?: string;
  explanation_text?: string;
  feature_columns?: string[];
  endpoint_url?: string;
  status: string;
  created_at: string;
}

export interface Student {
  id: number;
  student_code: string;
  full_name: string;
  department: string;
  attendance_pct: number;
  avg_marks: number;
  projects_count: number;
  certificates?: string[];
  performance_history?: { semester: string; gpa: number }[];
}

export interface ReportItem {
  id: number;
  title: string;
  report_type: string;
  summary_text: string;
  created_at: string;
}
