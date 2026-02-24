export interface User {
  id: number;
  email: string;
  role: "user" | "admin";
}

export interface Rider {
  source: string | null;
  source_url: string | null;
  name: string;
  nationality: string | null;
  birth_date: string | null;
  team: string | null;
  sanctions: string | null;
  instagram: string | null;
  notes: string | null;
  scraped_at: string | null;
  valid_from: string | null;
}

export interface Override {
  id: number;
  source: string | null;
  source_url: string | null;
  name: string | null;
  nationality: string | null;
  birth_date: string | null;
  sanctions: string | null;
  team: string | null;
  instagram: string | null;
  notes: string | null;
  is_manual_entry: boolean;
  manual_key: string | null;
  reason: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface AdminUser {
  id: number;
  email: string;
  role: "user" | "admin";
  created_at: string | null;
}
