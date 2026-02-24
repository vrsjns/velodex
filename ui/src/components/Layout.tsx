import { NavLink, Outlet, useNavigate } from "react-router-dom";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { useAuth } from "../context/AuthContext";

function UserIcon(): React.JSX.Element {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm-4.5 7a4.5 4.5 0 0 1 9 0H3.5z" />
    </svg>
  );
}

function ChevronDown(): React.JSX.Element {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <path d="M2 4l4 4 4-4" />
    </svg>
  );
}

export default function Layout(): React.JSX.Element {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

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
          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <button className="flex items-center gap-2 text-gray-300 text-sm hover:text-white bg-transparent border-none cursor-pointer outline-none">
                <UserIcon />
                {user.email}
                <ChevronDown />
              </button>
            </DropdownMenu.Trigger>
            <DropdownMenu.Portal>
              <DropdownMenu.Content
                align="end"
                sideOffset={8}
                className="bg-surface rounded shadow-md py-1 min-w-[160px] z-50"
              >
                <DropdownMenu.Item
                  onSelect={() => navigate("/profile")}
                  className="px-4 py-2 text-sm text-gray-700 cursor-pointer hover:bg-gray-100 outline-none"
                >
                  Profile
                </DropdownMenu.Item>
                <DropdownMenu.Separator className="my-1 border-t border-border" />
                <DropdownMenu.Item
                  onSelect={logout}
                  className="px-4 py-2 text-sm text-gray-700 cursor-pointer hover:bg-gray-100 outline-none"
                >
                  Logout
                </DropdownMenu.Item>
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        )}
      </nav>
      <div className="max-w-[1200px] mx-auto my-6 px-4">
        <Outlet />
      </div>
    </>
  );
}
