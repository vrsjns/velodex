import { createContext, useContext, useEffect, useState } from "react";
import type { User } from "../types";
import * as api from "../api";

interface AuthContextValue {
  user: User | null | undefined;
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
  register: (email: string, password: string) => Promise<User>;
  updateUser: (data: {
    email?: string;
    current_password?: string;
    new_password?: string;
  }) => Promise<User>;
}

interface AuthProviderProps {
  children: React.ReactNode;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: AuthProviderProps): React.JSX.Element {
  // undefined = loading, null = not authenticated, object = user
  const [user, setUser] = useState<User | null | undefined>(undefined);

  useEffect(() => {
    api
      .fetchMe()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  async function login(email: string, password: string): Promise<User> {
    const u = await api.login(email, password);
    setUser(u);
    return u;
  }

  async function register(email: string, password: string): Promise<User> {
    const u = await api.register(email, password);
    setUser(u);
    return u;
  }

  async function logout(): Promise<void> {
    await api.logout();
    setUser(null);
  }

  async function updateUser(data: {
    email?: string;
    current_password?: string;
    new_password?: string;
  }): Promise<User> {
    const updated = await api.updateProfile(data);
    setUser(updated);
    return updated;
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, register, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
