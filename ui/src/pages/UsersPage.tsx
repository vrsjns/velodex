import { useEffect, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { fetchUsers, updateUser, deleteUser } from "../api";
import { useAuth } from "../context/AuthContext";
import type { AdminUser } from "../types";
import { input, btnPrimary, btnSecondary, btnDanger, btnSm, formGroup, label, muted, errorText, successText } from "../styles";

const th = "bg-gray-100 font-semibold px-3 py-2 border border-border text-sm text-left";
const td = "px-3 py-2 border border-border text-sm";

export default function UsersPage(): React.JSX.Element {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [editForm, setEditForm] = useState<{ email: string; role: string; new_password: string }>({
    email: "",
    role: "user",
    new_password: "",
  });
  const [editError, setEditError] = useState("");
  const [editSuccess, setEditSuccess] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadUsers();
  }, []);

  async function loadUsers(): Promise<void> {
    try {
      setUsers(await fetchUsers());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  function openEdit(u: AdminUser): void {
    setEditing(u);
    setEditForm({ email: u.email, role: u.role, new_password: "" });
    setEditError("");
    setEditSuccess("");
  }

  function closeEdit(): void {
    setEditing(null);
    setEditError("");
    setEditSuccess("");
  }

  async function handleEditSave(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    if (!editing) return;
    setEditError("");
    setEditSuccess("");

    const data: { email?: string; role?: string; new_password?: string } = {};
    if (editForm.email !== editing.email) data.email = editForm.email;
    if (editForm.role !== editing.role) data.role = editForm.role;
    if (editForm.new_password) data.new_password = editForm.new_password;

    if (Object.keys(data).length === 0) {
      setEditError("No changes to save");
      return;
    }

    setSaving(true);
    try {
      await updateUser(editing.id, data);
      setEditSuccess("User updated");
      await loadUsers();
      setTimeout(() => closeEdit(), 800);
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function handleRoleChange(id: number, role: string): Promise<void> {
    try {
      await updateUser(id, { role });
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  async function handleDelete(id: number): Promise<void> {
    if (!confirm("Delete this user?")) return;
    try {
      await deleteUser(id);
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    }
  }

  return (
    <>
      <h1 className="mt-0">Users</h1>
      {error && <p className={errorText}>{error}</p>}
      <table className="w-full border-collapse bg-surface rounded-md shadow-sm overflow-hidden">
        <thead>
          <tr>
            <th className={th}>Email</th>
            <th className={th}>Role</th>
            <th className={th}>Created</th>
            <th className={th}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id} className="group">
              <td className={`${td} group-hover:bg-gray-50`}>{u.email}</td>
              <td className={`${td} group-hover:bg-gray-50`}>
                <select
                  value={u.role}
                  onChange={(e) => handleRoleChange(u.id, e.target.value)}
                  disabled={u.id === currentUser?.id}
                  className="px-2 py-1 border border-input rounded text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
              </td>
              <td className={`${td} group-hover:bg-gray-50 ${muted}`}>
                {u.created_at ? new Date(u.created_at).toLocaleDateString() : ""}
              </td>
              <td className={`${td} group-hover:bg-gray-50 whitespace-nowrap`}>
                <span className="inline-flex gap-1.5">
                  {u.id !== currentUser?.id && (
                    <>
                      <button
                        className={`${btnPrimary} ${btnSm}`}
                        onClick={() => openEdit(u)}
                      >
                        Edit
                      </button>
                      <button
                        className={`${btnDanger} ${btnSm}`}
                        onClick={() => handleDelete(u.id)}
                      >
                        Delete
                      </button>
                    </>
                  )}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <Dialog.Root open={editing !== null} onOpenChange={(open) => { if (!open) closeEdit(); }}>
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 bg-black/40 z-50" />
          <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-surface p-6 rounded-lg shadow-lg w-full max-w-[440px] z-50">
            <Dialog.Title className="text-lg font-semibold mt-0 mb-4">
              Edit User
            </Dialog.Title>
            <form onSubmit={handleEditSave} className="max-w-lg">
              <div className={formGroup}>
                <label className={label}>Email</label>
                <input
                  type="text"
                  className={input}
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                />
              </div>
              <div className={formGroup}>
                <label className={label}>Role</label>
                <select
                  className={input}
                  value={editForm.role}
                  onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                >
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <div className={formGroup}>
                <label className={label}>
                  New Password{" "}
                  <span className={muted}>(leave blank to keep current)</span>
                </label>
                <input
                  type="text"
                  className={input}
                  value={editForm.new_password}
                  onChange={(e) => setEditForm({ ...editForm, new_password: e.target.value })}
                />
              </div>
              {editError && <p className={errorText}>{editError}</p>}
              {editSuccess && <p className={successText}>{editSuccess}</p>}
              <div className="inline-flex gap-1.5">
                <button type="submit" className={btnPrimary} disabled={saving}>
                  {saving ? "Saving..." : "Save"}
                </button>
                <button type="button" className={btnSecondary} onClick={closeEdit}>
                  Cancel
                </button>
              </div>
            </form>
            <Dialog.Close className="absolute top-3 right-4 text-gray-400 hover:text-gray-600 text-xl leading-none cursor-pointer bg-transparent border-none" aria-label="Close">
              ✕
            </Dialog.Close>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </>
  );
}
