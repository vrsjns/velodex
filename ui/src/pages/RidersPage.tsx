import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchRiders } from "../api";
import type { Rider } from "../types";
import { btnPrimary, btnSecondary, muted } from "../styles";

const th = "bg-gray-100 font-semibold px-3 py-2 border border-gray-200 text-sm text-left";
const td = "px-3 py-2 border border-gray-200 text-sm";

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
      <h1 className="mt-0">Riders</h1>
      <form className="flex gap-2 max-w-xs mb-4" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Search by name..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 px-2.5 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button className={btnPrimary} type="submit">
          Search
        </button>
        {search && (
          <button className={btnSecondary} type="button" onClick={handleClear}>
            Clear
          </button>
        )}
      </form>
      {loading ? (
        <p className={muted}>Loading...</p>
      ) : riders.length === 0 ? (
        <p className={`${muted} text-center`}>No riders found.</p>
      ) : (
        <>
          <p className={`${muted} mb-4`}>{riders.length} riders</p>
          <table className="w-full border-collapse bg-white rounded-md shadow-sm overflow-hidden">
            <thead>
              <tr>
                <th className={th}>Name</th>
                <th className={th}>Nationality</th>
                <th className={th}>Birth date</th>
                <th className={th}>Team</th>
                <th className={th}>Sanctions</th>
                <th className={th}>Source</th>
                <th className={th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {riders.map((r, i) => (
                <tr key={i} className="group">
                  <td className={`${td} group-hover:bg-gray-50`}>{r.name}</td>
                  <td className={`${td} group-hover:bg-gray-50`}>{r.nationality}</td>
                  <td className={`${td} group-hover:bg-gray-50`}>{r.birth_date}</td>
                  <td className={`${td} group-hover:bg-gray-50`}>{r.team}</td>
                  <td className={`${td} group-hover:bg-gray-50`}>{r.sanctions}</td>
                  <td className={`${td} group-hover:bg-gray-50`}>
                    {r.source_url ? (
                      <a href={r.source_url} target="_blank" rel="noopener noreferrer">
                        {r.source || "link"}
                      </a>
                    ) : (
                      <span className={muted}>manual</span>
                    )}
                  </td>
                  <td className={`${td} group-hover:bg-gray-50 whitespace-nowrap`}>
                    {r.source_url && (
                      <Link
                        className={btnSecondary}
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
