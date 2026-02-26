import { Link } from "react-router-dom";

function Card(props: { to: string; title: string; desc: string; emoji: string }) {
  return (
    <Link
      to={props.to}
      className="group rounded-xl p-6 hover:shadow-2xl transition duration-300 backdrop-blur-md bg-white/5 border border-white/10 hover:border-indigo-400/30 hover:bg-white/10"
    >
      <div className="flex items-start gap-4">
        <div className="text-3xl bg-white/10 backdrop-blur-sm p-3 rounded-lg shadow-lg ring-1 ring-white/10">{props.emoji}</div>
        <div>
          <h3 className="font-semibold text-lg text-gray-200 group-hover:text-indigo-400 transition">{props.title}</h3>
          <p className="text-gray-400/90 mt-2">{props.desc}</p>
        </div>
      </div>
    </Link>
  );
}

export default function Home() {
  return (
    <div className="space-y-12 py-8 min-h-screen bg-gradient-to-br from-gray-900 via-indigo-950 to-purple-950">
      <section className="text-center max-w-3xl mx-auto space-y-4 p-8 rounded-2xl backdrop-blur-lg bg-white/5 border border-white/10 shadow-2xl">
        <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Sales Copilot</h1>
        <p className="text-gray-300/90 text-lg backdrop-blur-sm">
          Prepare for calls faster. Summarize anything, research companies, extract prospect insights,
          and generate a pre-call briefing — all powered by your local LLM.
        </p>
      </section>

      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-6 max-w-5xl mx-auto">
        <Card
          to="/summarize"
          title="Summarizer"
          desc="Paste any text and get concise bullets."
          emoji="📝"
        />
        <Card
          to="/company"
          title="Company Researcher"
          desc="Enter a website URL and get a focused summary."
          emoji="🏢"
        />
        <Card
          to="/prospect"
          title="Prospect Researcher"
          desc="Paste profile text to extract role, interests, and angles."
          emoji="🧑‍💼"
        />
        <Card
          to="/report"
          title="Pre-Call Report"
          desc="Combine company & prospect into a one-pager."
          emoji="📄"
        />
      </section>

      <section className="rounded-xl p-8 backdrop-blur-xl bg-white/5 border border-white/10 shadow-2xl max-w-3xl mx-auto">
        <h2 className="font-semibold text-xl mb-4 text-indigo-400">How it works</h2>
        <ol className="list-decimal ml-5 text-gray-300/90 space-y-2">
          <li>Frontend calls your FastAPI backend.</li>
          <li>Backend calls Ollama (local LLM) to generate summaries.</li>
          <li>Results are displayed as clean, readable cards.</li>
        </ol>
      </section>
    </div>
  );
}