import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import { Platform } from "react-native";
import {
  apiFetch,
  getToken,
  setToken,
  AuthResponse,
  User,
} from "@/src/api/client";

type AuthCtx = {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, nome?: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const Ctx = createContext<AuthCtx | null>(null);

// Função para obter o Expo Push Token e sincronizar com o Backend
async function syncPushToken() {
  try {
    // 1. Notificações nativas requerem dispositivo físico
    if (!Device.isDevice) {
      console.log("Push notifications não funcionam em emuladores.");
      return;
    }

    // 2. Configura canais de notificação no Android
    if (Platform.OS === "android") {
      await Notifications.setNotificationChannelAsync("default", {
        name: "default",
        importance: Notifications.AndroidImportance.MAX,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: "#FF231F7C",
      });
    }

    // 3. Verifica / Solicita permissões
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== "granted") {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== "granted") {
      console.log("Permissão para notificações push negada pelo utilizador.");
      return;
    }

    // 4. Obtém o token do dispositivo
    const tokenData = await Notifications.getExpoPushTokenAsync();
    const token = tokenData.data;

    console.log("====================================");
    console.log("SEU EXPO PUSH TOKEN:", token);
    console.log("====================================");

    // 5. Envia o token para salvar na tabela Usuarios do Azure SQL
    await apiFetch("/auth/push-token", {
      method: "POST",
      body: JSON.stringify({ push_token: token }),
    });

    console.log("Push token sincronizado com sucesso no backend!");
  } catch (err) {
    console.error("Erro ao sincronizar Push Token:", err);
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const t = await getToken();
      if (t) {
        try {
          const me = await apiFetch<User>("/auth/me");
          setUser(me);
          // Sincroniza o token se o utilizador já iniciou sessão anteriormente
          await syncPushToken();
        } catch {
          await setToken(null);
        }
      }
      setLoading(false);
    })();
  }, []);

  const value = useMemo<AuthCtx>(
    () => ({
      user,
      loading,
      signIn: async (email, password) => {
        const r = await apiFetch<AuthResponse>("/auth/login", {
          method: "POST",
          body: JSON.stringify({ email, password }),
        });
        await setToken(r.access_token);
        setUser(r.user);
        // Sincroniza o Push Token logo após o login
        await syncPushToken();
      },
      signUp: async (email, password, nome) => {
        const r = await apiFetch<AuthResponse>("/auth/register", {
          method: "POST",
          body: JSON.stringify({ email, password, nome }),
        });
        await setToken(r.access_token);
        setUser(r.user);
        // Sincroniza o Push Token logo após o registo
        await syncPushToken();
      },
      signOut: async () => {
        await setToken(null);
        setUser(null);
      },
    }),
    [user, loading]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth must be used within AuthProvider");
  return c;
}