import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="mx-auto mt-24 max-w-[1800px] border-t border-white/10 px-4 pb-24 pt-8 text-xs text-muted md:px-10 md:pb-10">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        <a href="https://www.themoviedb.org" target="_blank" rel="noreferrer" aria-label="The Movie Database">
          <img
            src="https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg"
            alt="TMDB"
            className="h-3"
            loading="lazy"
          />
        </a>
        <span>This product uses the TMDB API but is not endorsed or certified by TMDB.</span>
        <span>Ratings data: MovieLens (GroupLens). Awards: Wikidata.</span>
        <Link to="/lab" className="ml-auto hover:text-white">Research Lab</Link>
      </div>
    </footer>
  );
}