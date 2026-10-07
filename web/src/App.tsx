import { Route, Routes } from "react-router-dom";
import NavBar from "./components/NavBar";
import Home from "./pages/Home";
import Placeholder from "./pages/Placeholder";

export default function App() {
  return (
    <div className="min-h-screen bg-[#080808] text-white">
      <NavBar />
      <main className="px-6 py-8">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/discover" element={<Placeholder title="Discover" />} />
          <Route path="/genres" element={<Placeholder title="Genres" />} />
          <Route path="/my-list" element={<Placeholder title="My List" />} />
          <Route path="/activity" element={<Placeholder title="Activity" />} />
          <Route path="*" element={<Placeholder title="Not found" />} />
        </Routes>
      </main>
    </div>
  );
}