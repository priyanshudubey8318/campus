"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { User, LoginPayload, RegisterPayload } from "@/types/auth";
import { api, ApiError, setClientAuthToken } from "@/lib/api/client";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => Promise<void>;
  hasRole: (roleOrRoles: string | string[]) => boolean;
  hasPermission: (permOrPerms: string | string[]) => boolean;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const refreshUser = useCallback(async () => {
    try {
      const currentUser = await api.getMe();
      setUser(currentUser);
    } catch {
      setUser(null);
      setClientAuthToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(
    async (payload: LoginPayload): Promise<User> => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.login(payload);
        setUser(response.user);
        return response.user;
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Login failed. Please check your credentials.";
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const register = useCallback(
    async (payload: RegisterPayload): Promise<User> => {
      setIsLoading(true);
      setError(null);
      try {
        const registeredUser = await api.register(payload);
        // Automatically login after successful registration
        await login({ email: payload.email, password: payload.password });
        return registeredUser;
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Registration failed. Please try again.";
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [login]
  );

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await api.logout();
    } catch {
      // Ignore logout errors and clean local state
    } finally {
      setUser(null);
      setIsLoading(false);
    }
  }, []);

  const hasRole = useCallback(
    (roleOrRoles: string | string[]): boolean => {
      if (!user) return false;
      if (user.roles.includes("SUPER_ADMIN")) return true;

      const rolesToCheck = Array.isArray(roleOrRoles)
        ? roleOrRoles
        : [roleOrRoles];
      return rolesToCheck.some((r) => user.roles.includes(r.toUpperCase()));
    },
    [user]
  );

  const hasPermission = useCallback(
    (permOrPerms: string | string[]): boolean => {
      if (!user) return false;
      if (user.roles.includes("SUPER_ADMIN")) return true;

      const permsToCheck = Array.isArray(permOrPerms)
        ? permOrPerms
        : [permOrPerms];
      return permsToCheck.every((p) => user.permissions.includes(p));
    },
    [user]
  );

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      error,
      login,
      register,
      logout,
      hasRole,
      hasPermission,
      refreshUser,
      clearError,
    }),
    [
      user,
      isLoading,
      error,
      login,
      register,
      logout,
      hasRole,
      hasPermission,
      refreshUser,
      clearError,
    ]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
