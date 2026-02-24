import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import RidersPage from "./pages/RidersPage";
import OverridesPage from "./pages/OverridesPage";
import OverrideForm from "./pages/OverrideForm";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import UsersPage from "./pages/UsersPage";
import ProfilePage from "./pages/ProfilePage";

interface GuardProps {
  children: React.ReactNode;
}

function RequireAuth({ children }: GuardProps): React.JSX.Element | null {
  const { user } = useAuth();
  if (user === undefined) return null; // loading
  if (user === null) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function RequireAdmin({ children }: GuardProps): React.JSX.Element | null {
  const { user } = useAuth();
  if (user === undefined) return null;
  if (!user || user.role !== "admin") return <Navigate to="/riders" replace />;
  return <>{children}</>;
}

export default function App(): React.JSX.Element {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Navigate to="/riders" replace />} />
        <Route path="/riders" element={<RidersPage />} />
        <Route path="/overrides" element={<OverridesPage />} />
        <Route path="/overrides/new" element={<OverrideForm />} />
        <Route path="/overrides/:id/edit" element={<OverrideForm />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route
          path="/admin/users"
          element={
            <RequireAdmin>
              <UsersPage />
            </RequireAdmin>
          }
        />
      </Route>
    </Routes>
  );
}
