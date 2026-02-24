import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { btnSecondary, btnSm } from "../styles";

export default function Layout(): React.JSX.Element {
  const { user, logout } = useAuth();

  return (
    <>
      <nav className="bg-nav flex items-center gap-6 px-6 py-3">
        <NavLink to="/riders" className="text-lg font-bold text-white no-underline hover:no-underline">
          Velodex
        </NavLink>
        <NavLink
          to="/riders"
          className={({ isActive }) =>
            isActive ? "text-white no-underline" : "text-gray-300 no-underline hover:text-white"
          }
        >
          Riders
        </NavLink>
        <NavLink
          to="/overrides"
          className={({ isActive }) =>
            isActive ? "text-white no-underline" : "text-gray-300 no-underline hover:text-white"
          }
        >
          Overrides
        </NavLink>
        {user?.role === "admin" && (
          <NavLink
            to="/admin/users"
            className={({ isActive }) =>
              isActive ? "text-white no-underline" : "text-gray-300 no-underline hover:text-white"
            }
          >
            Users
          </NavLink>
        )}
        <div className="flex-grow" />
        {user && (
          <>
            <NavLink
              to="/profile"
              className={({ isActive }) =>
                isActive
                  ? "text-white text-sm no-underline"
                  : "text-gray-300 text-sm no-underline hover:text-white"
              }
            >
              {user.email}
            </NavLink>
            <button className={`${btnSecondary} ${btnSm}`} onClick={logout}>
              Logout
            </button>
          </>
        )}
      </nav>
      <div className="max-w-[1200px] mx-auto my-6 px-4">
        <Outlet />
      </div>
    </>
  );
}
