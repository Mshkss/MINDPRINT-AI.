export async function api<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch("/api" + path, {
    method,
    credentials: "include",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const data = await response
    .json()
    .catch(() => ({ detail: "Сервер недоступен" }));
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Проверьте заполнение полей",
    );
  return data as T;
}
export type User = {
  id: number;
  name: string;
  email: string;
  role: "patient" | "psychologist" | "admin";
};
export type Consent = {
  consent_status: boolean;
  share_journal: boolean;
  share_analytics: boolean;
  share_exercises: boolean;
};
export type Plan = {
  focus_areas: string[];
  goals: string[];
  allowed_exercises: string[];
  reminders_enabled: boolean;
  reminder_frequency: "daily" | "weekly";
};
export type Patient = User & {
  entries: number | null;
  weekly_entries: number | null;
  report_count: number | null;
  latest: string | null;
  completed: number | null;
  total: number | null;
  consent: Consent;
  plan?: Plan;
};
export type Entry = {
  id: number;
  content: string;
  mood_score: number;
  tags: string[];
  created_at: string;
  analysis_status: string;
};
export type Exercise = {
  id: number;
  name: string;
  description: string;
  type: string;
  steps: string[];
};
export type Assignment = {
  id: number;
  status: string;
  answers: string[];
  exercise: Exercise;
  available: boolean;
  completed_at: string | null;
};
export type Observation = {
  id: number;
  journal_entry_id: number;
  observation_type: string;
  observation_data: { text: string };
  evidence: string;
  feedback: string | null;
};
export type Analytics = {
  days: number;
  series: { date: string; mood: number; entries: number }[];
  entry_count: number;
  average_mood: number | null;
  topics: { name: string; count: number }[];
  observations: Observation[];
  completed_count: number;
  assignment_count: number;
  exercises_shared: boolean;
};
export type Report = {
  id: number;
  created_at: string;
  report_data: Analytics & {
    summary: string;
    questions: string[];
    disclaimer: string;
    provider: string;
  };
};
export type Message = {
  id: number;
  role: string;
  content: string;
  created_at: string;
};
export type ChatHistory = {
  sessions: { id: number; title: string; created_at: string }[];
  messages: Message[];
};
export const date = (value: string) =>
  new Date(value).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
  });
export const DEMO_MESSAGE =
  "Мне снова очень тревожно из-за работы. Кажется, что начальник хочет меня уволить";
