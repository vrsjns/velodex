import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchOverrides, deleteOverride } from "../api";
import type { Override } from "../types";

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
      <h1>Overrides</h1>
      <div className="mb-1">
        <Link className="btn btn-primary" to="/overrides/new">
          New override
        </Link>
      </div>
      {loading ? (
        <p className="muted">Loading...</p>
      ) : overrides.length === 0 ? (
        <p className="muted" style={{ textAlign: "center" }}>
          No overrides yet.
        </p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Source / Key</th>
              <th>Team</th>
              <th>Reason</th>
              <th>Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {overrides.map((o) => (
              <tr key={o.id}>
                <td>{o.name}</td>
                <td>{o.is_manual_entry ? "Manual" : "Correction"}</td>
                <td>
                  {o.is_manual_entry ? (
                    o.manual_key
                  ) : o.source_url ? (
                    <a
                      href={o.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {o.source || "link"}
                    </a>
                  ) : (
                    <span className="muted">-</span>
                  )}
                </td>
                <td>{o.team}</td>
                <td>{o.reason}</td>
                <td className="muted">
                  {o.updated_at
                    ? new Date(o.updated_at).toLocaleDateString()
                    : ""}
                </td>
                <td className="actions">
                  <span className="gap-sm">
                    <Link
                      className="btn btn-secondary"
                      to={`/overrides/${o.id}/edit`}
                    >
                      Edit
                    </Link>
                    <button
                      className="btn btn-danger"
                      onClick={() => handleDelete(o.id)}
                    >
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
