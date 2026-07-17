"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { api, getToken, setToken } from "@/lib/api";

const EMAIL_KEY = "sentinel-email";

type AuthState = {
  authenticated: boolean;
  email: string | null;
  ready: boolean;
  loginWithApiKey: (apiKey: string, email?: string) => Promise<void>;
  register: (email: string) => Promise<{ api_key: string }>;
  logout: () => void;
};

const AuthContext = createContext<AuthState>({
  authenticated: false,
  email: null,
  ready: false,
  loginWithApiKey: async () => {},
  register: async () => ({ api_key: "" }),
  logout: () => {},
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authenticated, setAuthenticated] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setAuthenticated(!!getToken());
    try {
      setEmail(localStorage.getItem(EMAIL_KEY));
    } catch {
      /* ignore */
    }
    setReady(true);
  }, []);

  const loginWithApiKey = useCallback(async (apiKey: string, mail?: string) => {
    const { access_token } = await api.token(apiKey);
    setToken(access_token);
    setAuthenticated(true);
    if (mail) {
      try {
        localStorage.setItem(EMAIL_KEY, mail);
      } catch {
        /* ignore */
      }
      setEmail(mail);
    }
  }, []);

  const register = useCallback(async (mail: string) => {
    const res = await api.register(mail);
    return { api_key: res.api_key };
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    try {
      localStorage.removeItem(EMAIL_KEY);
    } catch {
      /* ignore */
    }
    setAuthenticated(false);
    setEmail(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{ authenticated, email, ready, loginWithApiKey, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}
