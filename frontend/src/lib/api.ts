import { supabase } from "./supabase";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) ?? "http://localhost:8000/api";

/** Fetch wrapper. Attaches the Supabase JWT for creator endpoints when signed in. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");

  if (supabase) {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }

  const resp = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body?.error?.message ?? `Request failed (${resp.status})`);
  }
  return resp.json() as Promise<T>;
}

export interface Health {
  status: string;
  service: string;
  version: string;
  environment: string;
  supabase_configured: boolean;
}

export const getHealth = () => apiFetch<Health>("/health");

// --- Catch-ups ---------------------------------------------------------------

export type CatchupType = "casual" | "food" | "activity" | "outing" | "trip";

export interface SlotIn {
  starts_at: string; // ISO 8601
  ends_at: string;
  label?: string;
}

export interface CatchupCreate {
  title: string;
  message?: string;
  location?: string;
  type: CatchupType;
  slots: SlotIn[];
  deadline?: string;
  max_responses?: number;
}

export interface CatchupCreated {
  id: string;
  link_token: string;
  result_token: string;
  invite_url: string;
  result_url: string;
}

export const createCatchup = (body: CatchupCreate) =>
  apiFetch<CatchupCreated>("/catchups", { method: "POST", body: JSON.stringify(body) });

// --- Responder (anonymous) ---------------------------------------------------

export interface SlotOut {
  id: string;
  starts_at: string;
  ends_at: string;
  label?: string | null;
  sort_order?: number;
}

export interface InviteSummary {
  title: string;
  message?: string | null;
  location?: string | null;
  type: CatchupType;
  creator_first_name?: string | null;
  deadline?: string | null;
  status: string;
  slots: SlotOut[];
}

export interface ResponseSubmit {
  name: string;
  slot_ids: string[];
  companions: number;
  budget_min: number;
  budget_max: number;
  contribution?: number;
  interests?: string[];
  website?: string; // honeypot, always empty for real users
}

export const getInvite = (token: string) => apiFetch<InviteSummary>(`/invite/${token}`);

export const submitResponse = (token: string, body: ResponseSubmit) =>
  apiFetch<{ ok: boolean }>(`/invite/${token}/responses`, {
    method: "POST",
    body: JSON.stringify(body),
  });

// --- Results -----------------------------------------------------------------

export interface MoneyBand {
  low: number;
  high: number;
}

export interface BestSlot {
  id: string;
  starts_at: string;
  ends_at: string;
  label?: string | null;
  attending_headcount: number;
  attending_people: number;
}

export interface Alternative {
  id: string;
  starts_at: string;
  ends_at: string;
  label?: string | null;
  attending_headcount: number;
}

export interface BudgetResult {
  per_person: MoneyBand;
  total: MoneyBand;
  currency: string;
  inclusion_pct: number;
  contributions_total: number;
  method: string;
}

export interface SuggestionResult {
  title: string;
  blurb: string;
  est_per_person: MoneyBand;
  tags: string[];
}

export interface ResultOut {
  best_slot: BestSlot | null;
  alternatives: Alternative[];
  group_size: number;
  budget: BudgetResult | null;
  suggestions: SuggestionResult[];
  rationale: string | null;
  responded: string[];
  response_count: number;
  message: string | null;
}

export const getResults = (resultToken: string) =>
  apiFetch<ResultOut>(`/results/${resultToken}`);

export const closeCatchup = (catchupId: string) =>
  apiFetch<{ status: string }>(`/catchups/${catchupId}/close`, { method: "POST" });
