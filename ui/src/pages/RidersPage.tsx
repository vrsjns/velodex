import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchRiders } from "../api";
import type { Rider } from "../types";
import { btnPrimary, btnSecondary, muted, pageTitle } from "../styles";

const th = "bg-gray-100 font-semibold px-3 py-2 border border-border text-sm text-left";
const td = "px-3 py-3 border border-border text-sm";

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
      <h1 className={pageTitle}>Riders</h1>
      <form className="flex gap-2 w-full sm:max-w-xs mb-4" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Search by name..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 px-2.5 py-1.5 border border-input rounded text-sm focus:outline-none focus:ring-2 focus:ring-brand"
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

          {/* Mobile cards */}
          <div className="sm:hidden space-y-3">
            {riders.map((r, i) => (
              <div key={i} className="bg-surface rounded-md shadow-sm p-4">
                <div className="font-medium text-sm">{r.name}</div>
                <div className={`text-xs mt-1 ${muted}`}>{r.nationality}{r.birth_date ? ` · ${r.birth_date}` : ""}</div>
                {r.team && <div className="text-sm mt-1">{r.team}</div>}
                {r.sanctions && <div className={`text-xs mt-1 ${muted}`}>Sanctions: {r.sanctions}</div>}
                {r.source_url && (
                  <div className="mt-3">
                    <Link
                      className={btnSecondary}
                      to={`/overrides/new?source=${encodeURIComponent(r.source || "")}&source_url=${encodeURIComponent(r.source_url || "")}`}
                    >
                      Override
                    </Link>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Desktop table */}
          <div className="hidden sm:block overflow-x-auto">
            <table className="w-full border-collapse bg-surface rounded-md shadow-sm overflow-hidden">
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
                    <td className={`${td} group-hover:bg-blue-50 whitespace-nowrap`}>
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
          </div>
        </>
      )}
    </>
  );
}
