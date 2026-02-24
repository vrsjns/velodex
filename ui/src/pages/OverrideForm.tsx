import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { fetchOverride, createOverride, updateOverride } from "../api";

interface OverrideFormData {
  source: string;
  source_url: string;
  name: string;
  nationality: string;
  birth_date: string;
  sanctions: string;
  team: string;
  instagram: string;
  notes: string;
  is_manual_entry: boolean;
  manual_key: string;
  reason: string;
}

const EMPTY: OverrideFormData = {
  source: "",
  source_url: "",
  name: "",
  nationality: "",
  birth_date: "",
  sanctions: "",
  team: "",
  instagram: "",
  notes: "",
  is_manual_entry: false,
  manual_key: "",
  reason: "",
};

export default function OverrideForm(): React.JSX.Element {
  const { id: idParam } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isEdit = Boolean(idParam);
  const id = idParam ? parseInt(idParam, 10) : undefined;

  const [form, setForm] = useState<OverrideFormData>(() => ({
    ...EMPTY,
    source: searchParams.get("source") || "",
    source_url: searchParams.get("source_url") || "",
  }));
  const [loading, setLoading] = useState(isEdit);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isEdit || id === undefined) return;
    fetchOverride(id)
      .then((data) => {
        const filled = { ...EMPTY };
        for (const key of Object.keys(EMPTY) as Array<keyof OverrideFormData>) {
          const val = data[key as keyof typeof data];
          if (val != null) {
            (filled[key] as typeof val) = val;
          }
        }
        setForm(filled);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Load failed"))
      .finally(() => setLoading(false));
  }, [id, isEdit]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void {
    const { name, value } = e.target;
    const checked = e.target instanceof HTMLInputElement ? e.target.checked : false;
    const newValue = e.target.type === "checkbox" ? checked : value;
    setForm((prev) => ({ ...prev, [name]: newValue }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setError(null);
    try {
      if (isEdit && id !== undefined) {
        await updateOverride(id, form);
      } else {
        await createOverride(form);
      }
      navigate("/overrides");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    }
  }

  if (loading) return <p className="muted">Loading...</p>;

  return (
    <>
      <h1>{isEdit ? "Edit override" : "New override"}</h1>
      {error && <p style={{ color: "#dc2626" }}>{error}</p>}
      <form className="override-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>
            <input
              type="checkbox"
              name="is_manual_entry"
              checked={form.is_manual_entry}
              onChange={handleChange}
            />
            Manual entry (not linked to a scraped rider)
          </label>
        </div>

        {form.is_manual_entry ? (
          <div className="form-group">
            <label htmlFor="manual_key">Manual key</label>
            <input
              type="text"
              id="manual_key"
              name="manual_key"
              value={form.manual_key}
              onChange={handleChange}
            />
          </div>
        ) : (
          <>
            <div className="form-group">
              <label htmlFor="source">Source</label>
              <input
                type="text"
                id="source"
                name="source"
                value={form.source}
                onChange={handleChange}
              />
            </div>
            <div className="form-group">
              <label htmlFor="source_url">Source URL</label>
              <input
                type="text"
                id="source_url"
                name="source_url"
                value={form.source_url}
                onChange={handleChange}
              />
            </div>
          </>
        )}

        <div className="form-group">
          <label htmlFor="name">Name</label>
          <input
            type="text"
            id="name"
            name="name"
            value={form.name}
            onChange={handleChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="nationality">Nationality</label>
          <input
            type="text"
            id="nationality"
            name="nationality"
            value={form.nationality}
            onChange={handleChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="birth_date">Birth date</label>
          <input
            type="text"
            id="birth_date"
            name="birth_date"
            value={form.birth_date}
            onChange={handleChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="sanctions">Sanctions</label>
          <input
            type="text"
            id="sanctions"
            name="sanctions"
            value={form.sanctions}
            onChange={handleChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="team">Team</label>
          <input
            type="text"
            id="team"
            name="team"
            value={form.team}
            onChange={handleChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="instagram">Instagram</label>
          <input
            type="text"
            id="instagram"
            name="instagram"
            value={form.instagram}
            onChange={handleChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            name="notes"
            rows={3}
            value={form.notes}
            onChange={handleChange}
          />
        </div>
        <div className="form-group">
          <label htmlFor="reason">Reason for override</label>
          <textarea
            id="reason"
            name="reason"
            rows={2}
            value={form.reason}
            onChange={handleChange}
          />
        </div>

        <div className="gap-sm">
          <button className="btn btn-primary" type="submit">
            {isEdit ? "Update" : "Create"}
          </button>
          <button
            className="btn btn-secondary"
            type="button"
            onClick={() => navigate("/overrides")}
          >
            Cancel
          </button>
        </div>
      </form>
    </>
  );
}
