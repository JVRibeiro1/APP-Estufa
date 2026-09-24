import { storage } from "@/src/utils/storage";

// 1. Lê a variável EXPO_PUBLIC_API_URL e define o IP atual como fallback seguro
const BASE = process.env.EXPO_PUBLIC_API_URL || "http://192.168.90.16:8000/api";
const TOKEN_KEY = "alface_ai_token";

export async function getToken(): Promise<string | null> {
  return storage.secureGet(TOKEN_KEY, null);
}

export async function setToken(token: string | null): Promise<void> {
  if (token) {
    await storage.secureSet(TOKEN_KEY, token);
  } else {
    await storage.secureRemove(TOKEN_KEY);
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

  // 2. Garante a limpeza do path para não duplicar '/api' na URL final
  const cleanPath = path.startsWith("/api") ? path.replace("/api", "") : path;
  const targetPath = cleanPath.startsWith("/") ? cleanPath : `/${cleanPath}`;
  const url = `${BASE}${targetPath}`;

  // Log para visualizar no terminal do Expo a URL exata sendo chamada
  console.log("--> REQUISITANDO:", url);

  const res = await fetch(url, { ...init, headers });
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

// Tipagens alinhadas com o SQL Server e Pydantic
export type User = {
  Id: number;
  Email: string;
  Nome?: string | null;
  Adm?: boolean; 
  adm?: boolean;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type SensorReading = {
  Id: number;
  DeviceId: string;
  Temperatura?: number | null;
  Umidade?: number | null;
  Luminosidade?: number | null;
  DataHoraEnvio: string;
};

export type Alert = {
  id: string;
  disease: string;
  confidence: number;
  severity: "error" | "warning";
  plant_zone: string;
  image_url?: string | null;
  image_base64?: string | null;
  created_at: string;
  read: boolean;
  resolved: boolean;
};

export async function fetchLatestSensors(estufaId: number): Promise<SensorReading> {
  return await apiFetch<SensorReading>(`/sensors/latest?estufa_id=${estufaId}`);
}

export async function fetchSensorsHistory(estufaId: number, limit = 50): Promise<SensorReading[]> {
  return await apiFetch<SensorReading[]>(`/sensors/history?estufa_id=${estufaId}&limit=${limit}`);
}

export type Estufa = {
  Id: number;
  NomeEstufa: string;
};

export async function fetchMyGreenhouses(): Promise<Estufa[]> {
  return await apiFetch<Estufa[]>("/estufas/my-estufas");
}

export type CreateTeamUserPayload = {
  email: string;
  nome: string;
  senha: string;
  estufa_ids: number[];
  adm?: boolean;
};

export async function createTeamUser(payload: CreateTeamUserPayload) {
  return await apiFetch("/admin/team-users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchAlerts(estufaId: number): Promise<Alert[]> {
  return await apiFetch<Alert[]>(`/vision/alerts?estufa_id=${estufaId}`);
}

export async function fetchUnreadAlertsCount(estufaId: number): Promise<{ count: number }> {
  return await apiFetch<{ count: number }>(`/vision/alerts/unread-count?estufa_id=${estufaId}`);
}