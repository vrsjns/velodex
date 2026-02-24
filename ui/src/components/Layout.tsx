import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout(): React.JSX.Element {
  const { user, logout } = useAuth();

  return (
    <>
      <nav className="navbar">
        <NavLink to="/riders" className="brand">
          Velodex
        </NavLink>
        <NavLink to="/riders">Riders</NavLink>
        <NavLink to="/overrides">Overrides</NavLink>
        {user?.role === "admin" && <NavLink to="/admin/users">Users</NavLink>}
        <div className="spacer" />
        {user && (
          <>
            <NavLink to="/profile" className="nav-user">{user.email}</NavLink>
            <button className="btn btn-secondary btn-sm" onClick={logout}>
              Logout
            </button>
          </>
        )}
      </nav>
      <div className="container">
        <Outlet />
      </div>
    </>
  );
}
