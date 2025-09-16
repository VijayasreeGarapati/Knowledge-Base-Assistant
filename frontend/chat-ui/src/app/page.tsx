"use client";

import { useState } from "react";
import axios from "axios";

interface Message {
  role: "user" | "assistant";
  text: string;
  sources?: { source: string; content: string }[];
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const sendQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);

    setMessages((prev) => [...prev, { role: "user", text: query }]);

    try {
      const res = await axios.post("http://127.0.0.1:8000/query", {
        query,
        top_k: 3,
      });

      const answer = res.data.answer;
      const sources = res.data.sources;

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: answer, sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "⚠️ Error contacting backend." },
      ]);
    }

    setQuery("");
    setLoading(false);
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
              <p className="whitespace-pre-line">{msg.text}</p>
              {msg.sources && (
                <div className="mt-2 text-xs text-gray-600">
                  <b>Sources:</b>
                  <ul className="list-disc ml-4">
                    {msg.sources.map((s, j) => (
                      <li key={j}>{s.source}</li>
                    ))}
                  </ul>
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
