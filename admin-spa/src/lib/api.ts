import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { AuthResponse } from "../types";
import { useAuthStore } from "../store/auth";

const apiBaseURL = String(import.meta.env.VITE_API_BASE_URL || "");

export const api = axios.create({
  baseURL: apiBaseURL,
  timeout: 15000,
});

let refreshPromise: Promise<string | null> | null = null;

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

async function refreshAccessToken(): Promise<string | null> {
  const store = useAuthStore.getState();
  if (!store.refreshToken) {
    store.clearSession();
    return null;
  }

  if (!refreshPromise) {
    refreshPromise = api
      .post<AuthResponse>("/api/auth/refresh", { refresh_token: store.refreshToken })
      .then((response) => {
        const data = response.data;
        useAuthStore.getState().setSession(data.access_token, data.refresh_token, data.user);
        return data.access_token;
      })
      .catch(() => {
        useAuthStore.getState().clearSession();
        return null;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = (error.config || {}) as RetriableConfig;
    const responseStatus = error.response?.status;
    const url = String(original.url || "");

    const isAuthRequest =
      url.includes("/api/auth/login") ||
      url.includes("/api/auth/refresh");

    if (responseStatus !== 401 || original._retry || isAuthRequest) {
      return Promise.reject(error);
    }

    original._retry = true;
    const newToken = await refreshAccessToken();
    if (!newToken) {
      return Promise.reject(error);
    }

    original.headers = original.headers || {};
    original.headers.Authorization = `Bearer ${newToken}`;
    return api.request(original);
  },
);
