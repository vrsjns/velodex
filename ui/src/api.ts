import type { User, Rider, Override, AdminUser } from "./types";

const BASE = "/api";

async function request<T = unknown>(path: string, options: RequestInit = {}, retry = true): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    credentials: "same-origin",
    ...options,
  });
  if (res.status === 204) return null as T;
  if (res.status === 401 && retry) {
    try {
      await request<{ ok: boolean }>("/auth/refresh", { method: "POST" }, false);
      return request<T>(path, options, false);
    } catch {
      // refresh failed — fall through to throw below
    }
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// Auth
export function login(email: string, password: string): Promise<User> {
  return request<User>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function register(email: string, password: string): Promise<User> {
  return request<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function logout(): Promise<null> {
  return request<null>("/auth/logout", { method: "POST" });
}

export function fetchMe(): Promise<User> {
  return request<User>("/auth/me");
}

export function updateProfile(data: {
  email?: string;
  current_password?: string;
  new_password?: string;
}): Promise<User> {
  return request<User>("/auth/profile", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

// Riders
export function fetchRiders(q = ""): Promise<Rider[]> {
  const params = q ? `?q=${encodeURIComponent(q)}` : "";
  return request<Rider[]>(`/riders${params}`);
}

// Overrides
export function fetchOverrides(): Promise<Override[]> {
  return request<Override[]>("/overrides");
}

export function fetchOverride(id: number): Promise<Override> {
  return request<Override>(`/overrides/${id}`);
}

export function createOverride(data: Omit<Override, "id" | "created_at" | "updated_at">): Promise<Override> {
  return request<Override>("/overrides", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateOverride(id: number, data: Omit<Override, "id" | "created_at" | "updated_at">): Promise<Override> {
  return request<Override>(`/overrides/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteOverride(id: number): Promise<null> {
  return request<null>(`/overrides/${id}`, { method: "DELETE" });
}

// Admin
export function fetchUsers(): Promise<AdminUser[]> {
  return request<AdminUser[]>("/admin/users");
}

export function updateUser(id: number, data: {
  role?: string;
  email?: string;
  new_password?: string;
}): Promise<AdminUser> {
  return request<AdminUser>(`/admin/users/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteUser(id: number): Promise<null> {
  return request<null>(`/admin/users/${id}`, { method: "DELETE" });
}
