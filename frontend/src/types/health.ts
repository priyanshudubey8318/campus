export interface DatabaseHealth {
  connected: boolean;
  dialect: string;
  message: string;
}

export interface HealthResponse {
  status: "healthy" | "degraded" | string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  uptime_seconds: number;
  database: DatabaseHealth;
}
