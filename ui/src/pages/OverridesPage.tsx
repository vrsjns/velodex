import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchOverrides, deleteOverride } from "../api";
import type { Override } from "../types";
import { btnPrimary, btnSecondary, btnDanger, muted } from "../styles";

const th = "bg-gray-100 font-semibold px-3 py-2 border border-gray-200 text-sm text-left";
const td = "px-3 py-2 border border-gray-200 text-sm";

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
      <h1 className="mt-0">Overrides</h1>
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
        <table className="w-full border-collapse bg-white rounded-md shadow-sm overflow-hidden">
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
      )}
    </>
  );
}
