import AsyncStorage from "@react-native-async-storage/async-storage";

const BASE = process.env.EXPO_PUBLIC_BACKEND_URL;

const TOKEN_KEY = "alface_ai_token";

export async function getToken(): Promise<string | null> {
  return AsyncStorage.getItem(TOKEN_KEY);
}

export async function setToken(token: string | null): Promise<void> {
  if (token) {
    await AsyncStorage.setItem(TOKEN_KEY, token);
  } else {
    await AsyncStorage.removeItem(TOKEN_KEY);
  }
}

export async function apiFetch<T = any>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${BASE}/api${path}`, { ...init, headers });
  const text = await res.text();
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const msg =
      (data && (data.detail || data.message)) ||
      `Erro ${res.status}`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data as T;
}

// Types
export type User = { id: string; email: string; name?: string | null };
export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type SensorReading = {
  id: string;
  temperature: number;
  humidity: number;
  soil_moisture: number;
  light: number;
  co2: number;
  timestamp: string;
};

export type Alert = {
  id: string;
  disease: string;
  confidence: number;
  severity: "info" | "warning" | "error";
  plant_zone?: string | null;
  description?: string | null;
  recommendations?: string[];
  image_base64?: string | null;
  image_url?: string | null;
  read: boolean;
  resolved: boolean;
  created_at: string;
};
