import { FormEvent, useEffect, useRef, useState } from "react";
import { api, AskResponse, DocumentInfo, parseCitations } from "./api";

export default function App() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [active, setActive] = useState<number | null>(null);
  const [busy, setBusy] = useState<"upload" | "ask" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const refresh = () => api.listDocuments().then(setDocs).catch((e) => setError(e.message));
  useEffect(() => {
    refresh();
  }, []);

  async function run<T>(kind: "upload" | "ask", fn: () => Promise<T>) {
    setBusy(kind);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  }

  async function onUpload(files: FileList | null) {
    if (!files?.length) return;
    await run("upload", async () => {
      for (const file of Array.from(files)) await api.upload(file);
      await refresh();
    });
    if (fileInput.current) fileInput.current.value = "";
  }

  async function onAsk(e: FormEvent) {
    e.preventDefault();
    if (question.trim().length < 3) return;
    const res = await run("ask", () => api.ask(question.trim()));
    if (res) {
      setResult(res);
      setActive(null);
    }
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>ragdesk</h1>
        <p className="muted">Ask questions about your documents. Every answer cites its sources.</p>

        <label className="upload">
          <input
            ref={fileInput}
            type="file"
            accept=".pdf,.txt,.md"
            multiple
            onChange={(e) => onUpload(e.target.files)}
            disabled={busy !== null}
          />
          {busy === "upload" ? "Indexing…" : "Upload PDF, TXT or MD"}
        </label>

        <ul className="docs">
          {docs.length === 0 && <li className="muted">No documents yet.</li>}
          {docs.map((d) => (
            <li key={d.document_id}>
              <span title={d.filename}>{d.filename}</span>
              <small>{d.chunks} chunks</small>
              <button
                aria-label={`Remove ${d.filename}`}
                onClick={() => api.remove(d.document_id).then(refresh)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      </aside>

      <main className="main">
        <form onSubmit={onAsk} className="ask">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. How does Nav2 avoid obstacles?"
            aria-label="Question"
          />
          <button disabled={busy !== null || docs.length === 0}>
            {busy === "ask" ? "Thinking…" : "Ask"}
          </button>
        </form>

        {error && <div className="error">{error}</div>}

        {result && (
          <section className="result">
            <p className="answer">
              {parseCitations(result.answer).map((part, i) =>
                typeof part === "number" ? (
                  <button
                    key={i}
                    className={`cite ${active === part ? "on" : ""}`}
                    onClick={() => setActive(part)}
                  >
                    {part}
                  </button>
                ) : (
                  <span key={i}>{part}</span>
                ),
              )}
            </p>

            <h2>Sources</h2>
            <ol className="sources">
              {result.sources.map((s, i) => (
                <li key={i} className={active === i + 1 ? "on" : ""}>
                  <header>
                    <strong>
                      [{i + 1}] {s.document}
                    </strong>
                    <span>
                      page {s.page} · score {s.score.toFixed(2)}
                    </span>
                  </header>
                  <p>{s.text}</p>
                </li>
              ))}
            </ol>
          </section>
        )}
      </main>
    </div>
  );
}
