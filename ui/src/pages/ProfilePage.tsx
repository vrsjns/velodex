import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { input, btnPrimary, formGroup, label, errorText, successText } from "../styles";

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
      <h1 className="mt-0">Profile</h1>

      <div className="max-w-lg">
        <h2 className="mt-0">Change Email</h2>
        <form onSubmit={handleEmailSubmit}>
          <div className={formGroup}>
            <label className={label}>Email</label>
            <input
              type="email"
              className={input}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          {emailError && <p className={errorText}>{emailError}</p>}
          {emailSuccess && <p className={successText}>{emailSuccess}</p>}
          <button
            className={btnPrimary}
            disabled={emailLoading || email === user?.email}
          >
            {emailLoading ? "Saving…" : "Update Email"}
          </button>
        </form>

        <h2 className="mt-8">Change Password</h2>
        <form onSubmit={handlePasswordSubmit}>
          <div className={formGroup}>
            <label className={label}>Current Password</label>
            <input
              type="password"
              className={input}
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
          </div>
          <div className={formGroup}>
            <label className={label}>New Password</label>
            <input
              type="password"
              className={input}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </div>
          <div className={formGroup}>
            <label className={label}>Confirm New Password</label>
            <input
              type="password"
              className={input}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          {pwError && <p className={errorText}>{pwError}</p>}
          {pwSuccess && <p className={successText}>{pwSuccess}</p>}
          <button className={btnPrimary} disabled={pwLoading}>
            {pwLoading ? "Saving…" : "Update Password"}
          </button>
        </form>
      </div>
    </>
  );
}
