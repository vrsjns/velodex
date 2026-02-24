import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function ProfilePage(): React.JSX.Element {
  const { user, updateUser } = useAuth();

  const [email, setEmail] = useState(user?.email ?? "");
  const [emailError, setEmailError] = useState("");
  const [emailSuccess, setEmailSuccess] = useState("");
  const [emailLoading, setEmailLoading] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwError, setPwError] = useState("");
  const [pwSuccess, setPwSuccess] = useState("");
  const [pwLoading, setPwLoading] = useState(false);

  async function handleEmailSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setEmailError("");
    setEmailSuccess("");
    if (email === user?.email) return;
    setEmailLoading(true);
    try {
      await updateUser({ email });
      setEmailSuccess("Email updated successfully.");
    } catch (err) {
      setEmailError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setEmailLoading(false);
    }
  }

  async function handlePasswordSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setPwError("");
    setPwSuccess("");
    if (newPassword !== confirmPassword) {
      setPwError("New passwords do not match.");
      return;
    }
    setPwLoading(true);
    try {
      await updateUser({ current_password: currentPassword, new_password: newPassword });
      setPwSuccess("Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      setPwError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setPwLoading(false);
    }
  }

  return (
    <>
      <h1>Profile</h1>

      <div className="override-form">
        <h2>Change Email</h2>
        <form onSubmit={handleEmailSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          {emailError && <p className="error">{emailError}</p>}
          {emailSuccess && <p className="success">{emailSuccess}</p>}
          <button className="btn btn-primary" disabled={emailLoading || email === user?.email}>
            {emailLoading ? "Saving…" : "Update Email"}
          </button>
        </form>

        <h2 style={{ marginTop: "2rem" }}>Change Password</h2>
        <form onSubmit={handlePasswordSubmit}>
          <div className="form-group">
            <label>Current Password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          {pwError && <p className="error">{pwError}</p>}
          {pwSuccess && <p className="success">{pwSuccess}</p>}
          <button className="btn btn-primary" disabled={pwLoading}>
            {pwLoading ? "Saving…" : "Update Password"}
          </button>
        </form>
      </div>
    </>
  );
}
