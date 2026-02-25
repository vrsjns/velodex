import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchOverrides, deleteOverride } from "../api";
import type { Override } from "../types";
import { btnPrimary, btnSecondary, btnDanger, muted, pageTitle } from "../styles";

const th = "bg-gray-100 font-semibold px-3 py-2 border border-border text-sm text-left";
const td = "px-3 py-2 border border-border text-sm";

export default function OverridesPage(): React.JSX.Element {
  const [overrides, setOverrides] = useState<Override[]>([]);
  const [loading, setLoading] = useState(true);

  function load(): void {
    setLoading(true);
    fetchOverrides()
      .then(setOverrides)
      .finally(() => setLoading(false));
  }

  useEffect(load, []);

  async function handleDelete(id: number): Promise<void> {
    if (!confirm("Delete this override?")) return;
    await deleteOverride(id);
    load();
  }

  return (
    <>
      <h1 className={pageTitle}>Overrides</h1>
      <div className="mb-4">
        <Link className={btnPrimary} to="/overrides/new">
          New override
        </Link>
      </div>
      {loading ? (
        <p className={muted}>Loading...</p>
      ) : overrides.length === 0 ? (
        <p className={`${muted} text-center`}>No overrides yet.</p>
      ) : (
        <>
          {/* Mobile cards */}
          <div className="sm:hidden space-y-3">
            {overrides.map((o) => (
              <div key={o.id} className="bg-surface rounded-md shadow-sm p-4">
                <div className="font-medium text-sm">{o.name}</div>
                <div className={`text-xs mt-1 ${muted}`}>
                  {o.is_manual_entry ? "Manual" : "Correction"}
                  {o.updated_at ? ` · ${new Date(o.updated_at).toLocaleDateString()}` : ""}
                </div>
                {o.team && <div className="text-sm mt-1">{o.team}</div>}
                {o.reason && (
                  <div className={`text-xs mt-1 ${muted} line-clamp-2`}>{o.reason}</div>
                )}
                <div className="mt-3 inline-flex gap-1.5">
                  <Link className={btnSecondary} to={`/overrides/${o.id}/edit`}>
                    Edit
                  </Link>
                  <button className={btnDanger} onClick={() => handleDelete(o.id)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Desktop table */}
          <div className="hidden sm:block overflow-x-auto">
            <table className="w-full border-collapse bg-surface rounded-md shadow-sm overflow-hidden">
              <thead>
                <tr>
                  <th className={th}>Name</th>
                  <th className={th}>Type</th>
                  <th className={th}>Source / Key</th>
                  <th className={th}>Team</th>
                  <th className={th}>Reason</th>
                  <th className={th}>Updated</th>
                  <th className={th}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {overrides.map((o) => (
                  <tr key={o.id} className="group">
                    <td className={`${td} group-hover:bg-gray-50`}>{o.name}</td>
                    <td className={`${td} group-hover:bg-gray-50`}>
                      {o.is_manual_entry ? "Manual" : "Correction"}
                    </td>
                    <td className={`${td} group-hover:bg-gray-50`}>
                      {o.is_manual_entry ? (
                        o.manual_key
                      ) : o.source_url ? (
                        <a href={o.source_url} target="_blank" rel="noopener noreferrer">
                          {o.source || "link"}
                        </a>
                      ) : (
                        <span className={muted}>-</span>
                      )}
                    </td>
                    <td className={`${td} group-hover:bg-gray-50`}>{o.team}</td>
                    <td className={`${td} group-hover:bg-gray-50`}>{o.reason}</td>
                    <td className={`${td} group-hover:bg-gray-50 ${muted}`}>
                      {o.updated_at ? new Date(o.updated_at).toLocaleDateString() : ""}
                    </td>
                    <td className={`${td} group-hover:bg-gray-50 whitespace-nowrap`}>
                      <span className="inline-flex gap-1.5">
                        <Link className={btnSecondary} to={`/overrides/${o.id}/edit`}>
                          Edit
                        </Link>
                        <button className={btnDanger} onClick={() => handleDelete(o.id)}>
                          Delete
                        </button>
                      </span>
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
