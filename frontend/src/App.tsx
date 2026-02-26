import { Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Summarizer from "./features/summarize";
import Company from "./pages/Company";
import Prospect from "./pages/Prospect";
import Report from "./pages/Report";
// placeholders for now — replace later
// function Placeholder({ title }: { title: string }) {
//   return (
//     <div className="max-w-6xl mx-auto p-6">
//       <h1 className="text-xl font-semibold">{title}</h1>
//       <p className="text-gray-600 mt-2">Coming next…</p>
//     </div>
//   );
// }



export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-indigo-950 to-purple-950">
      <header className="sticky top-0 z-10 backdrop-blur-md bg-black/10 border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400">Sales Copilot</Link>
          <nav className="flex items-center gap-6">
            <Link to="/summarize" className="text-gray-400 hover:text-indigo-400 transition duration-300">Summarizer</Link>
            <Link to="/company" className="text-gray-400 hover:text-indigo-400 transition duration-300">Company</Link>
            <Link to="/prospect" className="text-gray-400 hover:text-indigo-400 transition duration-300">Prospect</Link>
            <Link to="/report" className="text-gray-400 hover:text-indigo-400 transition duration-300">Report</Link>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="*" element={
            <div className="backdrop-blur-sm bg-white/5 rounded-2xl border border-white/10 shadow-2xl p-6">
              <Routes>
                <Route path="/summarize" element={<Summarizer />} />
                <Route path="/company" element={<Company />} />
                <Route path="/prospect" element={<Prospect />} />
                <Route path="/report" element={<Report />} />
              </Routes>
            </div>
          } />
        </Routes>
      </main>
    </div>
  );
}