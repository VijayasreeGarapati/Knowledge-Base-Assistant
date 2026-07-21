"use client";

import { useState } from "react";

interface Source {
  source: string;
  content: string;
  page?: number;
}

interface Message {
  role: "user" | "assistant";
  text: string;
  sources?: Source[];
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const updateLastAssistant = (updater: (message: Message) => Message) => {
    setMessages((prev) => {
      const next = [...prev];
      for (let i = next.length - 1; i >= 0; i -= 1) {
        if (next[i].role === "assistant") {
          next[i] = updater(next[i]);
          break;
        }
      }
      return next;
    });
  };

  const sendStandardQuery = async (question: string) => {
    const res = await fetch("http://127.0.0.1:8000/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: question,
        top_k: 3,
      }),
    });

    if (!res.ok) {
      throw new Error("Backend request failed");
    }

    const data = await res.json();
    updateLastAssistant(() => ({
      role: "assistant",
      text: data.answer,
      sources: data.sources,
    }));
  };

  const sendQuery = async () => {
    if (!query.trim()) return;
    const question = query;
    setLoading(true);
    setQuery("");

    setMessages((prev) => [
      ...prev,
      { role: "user", text: question },
      { role: "assistant", text: "" },
    ]);

    try {
      const res = await fetch("http://127.0.0.1:8000/query/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: question,
          top_k: 3,
        }),
      });

      if (!res.ok || !res.body) {
        await sendStandardQuery(question);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      const handleEvent = (rawEvent: string) => {
        const event = rawEvent
          .split("\n")
          .find((line) => line.startsWith("event: "))
          ?.replace("event: ", "");
        const data = rawEvent
          .split("\n")
          .find((line) => line.startsWith("data: "))
          ?.replace("data: ", "");

        if (!event || !data) return;

        const parsed = JSON.parse(data);
        if (event === "sources") {
          updateLastAssistant((message) => ({ ...message, sources: parsed }));
        }
        if (event === "chunk") {
          updateLastAssistant((message) => ({
            ...message,
            text: `${message.text}${parsed.text}`,
          }));
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        events.forEach(handleEvent);
      }

      if (buffer) handleEvent(buffer);
    } catch {
      setMessages((prev) => {
        const next = [...prev];
        for (let i = next.length - 1; i >= 0; i -= 1) {
          if (next[i].role === "assistant") {
            next[i] = { role: "assistant", text: "⚠️ Error contacting backend." };
            return next;
          }
        }
        return [...next, { role: "assistant", text: "⚠️ Error contacting backend." }];
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-100 flex flex-col items-center p-6">
      <h2 className="text-3xl font-bold mb-6 text-gray-800">
        💡 Knowledge Base Assistant
      </h2>

      {/* Chat Window */}
      <div className="w-full max-w-2xl flex-1 border rounded-lg p-4 h-[500px] overflow-y-scroll bg-white shadow-md">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-4 flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 text-gray-900"
              }`}
            >
              <p className="whitespace-pre-line">
                {msg.text || (loading && msg.role === "assistant" ? "Thinking..." : "")}
              </p>
              {msg.sources && (
                <div className="mt-3 text-xs text-gray-700">
                  <b>Sources:</b>
                  <div className="mt-1 space-y-2">
                    {msg.sources.map((s, j) => (
                      <details key={j} className="rounded border border-gray-300 bg-white p-2">
                        <summary className="cursor-pointer font-medium">
                          {s.source}
                          {s.page ? `, page ${s.page}` : ""}
                        </summary>
                        <p className="mt-2 whitespace-pre-line text-gray-600">{s.content}</p>
                      </details>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="flex w-full max-w-2xl mt-4">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendQuery();
            }
          }}
          className="flex-1 border rounded-l-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
          placeholder="Ask me something..."
        />
        <button
          onClick={sendQuery}
          disabled={loading}
          className="px-6 py-3 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Thinking..." : "Send"}
        </button>
      </div>
    </main>
  );
}
