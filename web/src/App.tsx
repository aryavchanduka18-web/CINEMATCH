import { Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import Account from "./pages/Account";
import Activity from "./pages/Activity";
import { AuthPage } from "./pages/Auth";
import Discover from "./pages/Discover";
import { Genre, Genres } from "./pages/Genres";
import Home from "./pages/Home";
import Lab from "./pages/Lab";
import Movie from "./pages/Movie";
import MyList from "./pages/MyList";
import Onboarding from "./pages/Onboarding";
import Search from "./pages/Search";
import { PageMessage } from "./components/Loading";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<Home />} />
        <Route path="/discover" element={<Discover />} />
        <Route path="/genres" element={<Genres />} />
        <Route path="/genres/:slug" element={<Genre />} />
        <Route path="/movie/:id" element={<Movie />} />
        <Route path="/my-list" element={<MyList />} />
        <Route path="/activity" element={<Activity />} />
        <Route path="/search" element={<Search />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route path="/lab" element={<Lab />} />
        <Route path="/account" element={<Account />} />
        <Route path="*" element={<PageMessage title="Page not found" />} />
      </Route>
    </Routes>
  );
}