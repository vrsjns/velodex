import { useEffect, useState } from "react";
import { fetchUsers, updateUser, deleteUser } from "../api";
import { useAuth } from "../context/AuthContext";
import type { AdminUser } from "../types";

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
      <h1>Users</h1>
      {error && <p className="error">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Email</th>
            <th>Role</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.email}</td>
              <td>
                <select
                  value={u.role}
                  onChange={(e) => handleRoleChange(u.id, e.target.value)}
                  disabled={u.id === currentUser?.id}
                >
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
              </td>
              <td className="muted">
                {u.created_at ? new Date(u.created_at).toLocaleDateString() : ""}
              </td>
              <td className="actions">
                <span className="gap-sm">
                  {u.id !== currentUser?.id && (
                    <>
                      <button className="btn btn-primary btn-sm" onClick={() => openEdit(u)}>
                        Edit
                      </button>
                      <button className="btn btn-danger btn-sm" onClick={() => handleDelete(u.id)}>
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

      {editing && (
        <div className="modal-backdrop" onClick={closeEdit}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Edit User</h2>
            <form onSubmit={handleEditSave} className="override-form">
              <div className="form-group">
                <label>Email</label>
                <input
                  type="text"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  value={editForm.role}
                  onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                >
                  <option value="user">user</option>
                  <option value="admin">admin</option>
                </select>
              </div>
              <div className="form-group">
                <label>New Password <span className="muted">(leave blank to keep current)</span></label>
                <input
                  type="text"
                  value={editForm.new_password}
                  onChange={(e) => setEditForm({ ...editForm, new_password: e.target.value })}
                />
              </div>
              {editError && <p className="error">{editError}</p>}
              {editSuccess && <p className="success">{editSuccess}</p>}
              <div className="gap-sm">
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? "Saving..." : "Save"}
                </button>
                <button type="button" className="btn btn-secondary" onClick={closeEdit}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
