import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
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
      },
      signUp: async (email, password, nome) => {
        const r = await apiFetch<AuthResponse>("/auth/register", {
          method: "POST",
          body: JSON.stringify({ email, password, nome }), // Corrigido de 'name' para 'nome'
        });
        await setToken(r.access_token);
        setUser(r.user);
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