/**
 * Authentication and authorization TypeScript interface contracts.
 */

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  is_active: boolean;
  is_verified: boolean;
  roles: string[];
  permissions: string[];
  created_at: string;
  last_login_at?: string | null;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  role?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface MessageResponse {
  message: string;
}

export type UserRole =
  | "SUPER_ADMIN"
  | "ADMIN"
  | "FACULTY"
  | "ADVISOR"
  | "COUNSELOR"
  | "STUDENT"
  | "EXTERNAL_REPORTER";
