import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchRiders } from "../api";
import type { Rider } from "../types";

export default function RidersPage(): React.JSX.Element {
  const [riders, setRiders] = useState<Rider[]>([]);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchRiders(search)
      .then(setRiders)
      .finally(() => setLoading(false));
  }, [search]);

  function handleSubmit(e: React.FormEvent<HTMLFormElement>): void {
    e.preventDefault();
    setSearch(query);
  }

  function handleClear(): void {
    setQuery("");
    setSearch("");
  }

  return (
    <>
      <h1>Riders</h1>
      <form className="search-form" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Search by name..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="btn btn-primary" type="submit">
          Search
        </button>
        {search && (
          <button
            className="btn btn-secondary"
            type="button"
            onClick={handleClear}
          >
            Clear
          </button>
        )}
      </form>
      {loading ? (
        <p className="muted">Loading...</p>
      ) : riders.length === 0 ? (
        <p className="muted" style={{ textAlign: "center" }}>
          No riders found.
        </p>
      ) : (
        <>
          <p className="muted mb-1">{riders.length} riders</p>
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Nationality</th>
                <th>Birth date</th>
                <th>Team</th>
                <th>Sanctions</th>
                <th>Source</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {riders.map((r, i) => (
                <tr key={i}>
                  <td>{r.name}</td>
                  <td>{r.nationality}</td>
                  <td>{r.birth_date}</td>
                  <td>{r.team}</td>
                  <td>{r.sanctions}</td>
                  <td>
                    {r.source_url ? (
                      <a
                        href={r.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {r.source || "link"}
                      </a>
                    ) : (
                      <span className="muted">manual</span>
                    )}
                  </td>
                  <td className="actions">
                    {r.source_url && (
                      <Link
                        className="btn btn-secondary"
                        to={`/overrides/new?source=${encodeURIComponent(r.source || "")}&source_url=${encodeURIComponent(r.source_url || "")}`}
                      >
                        Override
                      </Link>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </>
  );
}
