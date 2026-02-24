import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { fetchOverride, createOverride, updateOverride } from "../api";
import { input, btnPrimary, btnSecondary, formGroup, label, muted } from "../styles";

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

  if (loading) return <p className={muted}>Loading...</p>;

  return (
    <>
      <h1 className="mt-0">{isEdit ? "Edit override" : "New override"}</h1>
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <form className="max-w-lg" onSubmit={handleSubmit}>
        <div className={formGroup}>
          <label className="inline-flex items-center gap-2 cursor-pointer text-sm font-medium">
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
          <div className={formGroup}>
            <label htmlFor="manual_key" className={label}>Manual key</label>
            <input type="text" id="manual_key" name="manual_key"
              className={input} value={form.manual_key} onChange={handleChange} />
          </div>
        ) : (
          <>
            <div className={formGroup}>
              <label htmlFor="source" className={label}>Source</label>
              <input type="text" id="source" name="source"
                className={input} value={form.source} onChange={handleChange} />
            </div>
            <div className={formGroup}>
              <label htmlFor="source_url" className={label}>Source URL</label>
              <input type="text" id="source_url" name="source_url"
                className={input} value={form.source_url} onChange={handleChange} />
            </div>
          </>
        )}

        <div className={formGroup}>
          <label htmlFor="name" className={label}>Name</label>
          <input type="text" id="name" name="name"
            className={input} value={form.name} onChange={handleChange} />
        </div>
        <div className={formGroup}>
          <label htmlFor="nationality" className={label}>Nationality</label>
          <input type="text" id="nationality" name="nationality"
            className={input} value={form.nationality} onChange={handleChange} />
        </div>
        <div className={formGroup}>
          <label htmlFor="birth_date" className={label}>Birth date</label>
          <input type="text" id="birth_date" name="birth_date"
            className={input} value={form.birth_date} onChange={handleChange} />
        </div>
        <div className={formGroup}>
          <label htmlFor="sanctions" className={label}>Sanctions</label>
          <input type="text" id="sanctions" name="sanctions"
            className={input} value={form.sanctions} onChange={handleChange} />
        </div>
        <div className={formGroup}>
          <label htmlFor="team" className={label}>Team</label>
          <input type="text" id="team" name="team"
            className={input} value={form.team} onChange={handleChange} />
        </div>
        <div className={formGroup}>
          <label htmlFor="instagram" className={label}>Instagram</label>
          <input type="text" id="instagram" name="instagram"
            className={input} value={form.instagram} onChange={handleChange} />
        </div>
        <div className={formGroup}>
          <label htmlFor="notes" className={label}>Notes</label>
          <textarea id="notes" name="notes" rows={3}
            className={`${input} resize-y`} value={form.notes} onChange={handleChange} />
        </div>
        <div className={formGroup}>
          <label htmlFor="reason" className={label}>Reason for override</label>
          <textarea id="reason" name="reason" rows={2}
            className={`${input} resize-y`} value={form.reason} onChange={handleChange} />
        </div>

        <div className="inline-flex gap-1.5">
          <button className={btnPrimary} type="submit">
            {isEdit ? "Update" : "Create"}
          </button>
          <button className={btnSecondary} type="button" onClick={() => navigate("/overrides")}>
            Cancel
          </button>
        </div>
      </form>
    </>
  );
}
