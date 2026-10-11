export interface DocumentInfo {
  document_id: string;
  filename: string;
  chunks: number;
}

export interface Source {
  document: string;
  page: number;
  score: number;
  text: string;
}

export interface AskResponse {
  answer: string;
  sources: Source[];
}

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = typeof body.detail === "string" ? body.detail : res.statusText;
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

export const api = {
  listDocuments: () => request<DocumentInfo[]>("/documents"),
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentInfo>("/documents", { method: "POST", body: form });
  },
  remove: (id: string) => request<void>(`/documents/${id}`, { method: "DELETE" }),
  ask: (question: string) =>
    request<AskResponse>("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
};

/** Split an answer like "foo [1] bar [2]" into text and citation parts for rendering. */
export function parseCitations(answer: string): Array<string | number> {
  return answer
    .split(/(\[\d+\])/)
    .filter((part) => part !== "")
    .map((part) => {
      const m = part.match(/^\[(\d+)\]$/);
      return m ? Number(m[1]) : part;
    });
}
