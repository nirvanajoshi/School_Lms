"use client";

import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import {
  HiOutlineBars3,
  HiOutlineBell,
  HiOutlineMagnifyingGlass,
  HiOutlineArrowRightOnRectangle,
} from "react-icons/hi2";

interface NavbarProps {
  onMenuClick: () => void;
  title?: string;
}

export default function Navbar({ onMenuClick, title }: NavbarProps) {
  const { user, profile, logout } = useAuth();
  const router = useRouter();
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header
      className="sticky top-0 z-30 bg-white/80 backdrop-blur-lg"
      style={{ borderBottom: "1px solid var(--color-gray-200)" }}
    >
      <div className="flex items-center justify-between h-[60px] px-4 sm:px-6">
        {/* Left */}
        <div className="flex items-center gap-3">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-[var(--radius-sm)] hover:bg-[var(--color-gray-100)] transition-colors"
          >
            <HiOutlineBars3 className="w-5 h-5 text-[var(--color-gray-500)]" />
          </button>
          {title && (
            <h1 className="text-[15px] font-semibold text-[var(--color-gray-900)] hidden sm:block">
              {title}
            </h1>
          )}
        </div>

        {/* Right */}
        <div className="flex items-center gap-1">
          {/* Search */}
          <div
            className="hidden md:flex items-center gap-2 px-3 h-[36px] rounded-[var(--radius-sm)] w-56"
            style={{ background: "var(--color-gray-50)", border: "1px solid var(--color-gray-200)" }}
          >
            <HiOutlineMagnifyingGlass className="w-4 h-4 text-[var(--color-gray-400)]" />
            <input
              type="text"
              placeholder="Search..."
              className="bg-transparent text-[13px] outline-none w-full placeholder:text-[var(--color-gray-400)]"
            />
          </div>

          {/* Notifications */}
          <button
            className="relative p-2 rounded-[var(--radius-sm)] hover:bg-[var(--color-gray-100)] transition-colors"
          >
            <HiOutlineBell className="w-[18px] h-[18px] text-[var(--color-gray-500)]" />
            <span
              className="absolute top-[7px] right-[7px] w-[7px] h-[7px] rounded-full"
              style={{ background: "var(--color-danger-500)", border: "2px solid white" }}
            />
          </button>

          {/* User menu */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-2 p-1.5 rounded-[var(--radius-sm)] hover:bg-[var(--color-gray-100)] transition-colors"
            >
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-white text-[13px] font-bold flex-shrink-0"
                style={{
                  background: `linear-gradient(135deg, var(--color-primary-400), var(--color-primary-600))`,
                }}
              >
                {profile?.full_name?.charAt(0) || user?.username?.charAt(0) || "U"}
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-[13px] font-semibold text-[var(--color-gray-900)] leading-tight">
                  {profile?.full_name || user?.username || "User"}
                </p>
                <p className="text-[11px] text-[var(--color-gray-400)] capitalize leading-tight">
                  {profile?.role || "student"}
                </p>
              </div>
            </button>

            {showDropdown && (
              <div
                className="absolute right-0 mt-2 w-52 rounded-[var(--radius-lg)] py-1 animate-fade-in"
                style={{
                  background: "var(--color-white)",
                  border: "1px solid var(--color-gray-200)",
                  boxShadow: "var(--shadow-lg)",
                }}
              >
                <div className="px-4 py-2.5" style={{ borderBottom: "1px solid var(--color-gray-100)" }}>
                  <p className="text-[13px] font-semibold text-[var(--color-gray-900)]">
                    {profile?.full_name || user?.username}
                  </p>
                  <p className="text-[11px] text-[var(--color-gray-400)]">{user?.email}</p>
                </div>
                <button
                  onClick={() => {
                    setShowDropdown(false);
                    router.push("/profile");
                  }}
                  className="w-full text-left px-4 py-2.5 text-[13px] font-medium text-[var(--color-gray-600)] hover:bg-[var(--color-gray-50)] transition-colors"
                >
                  Profile Settings
                </button>
                <div style={{ borderTop: "1px solid var(--color-gray-100)", margin: "4px 0" }} />
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2.5 text-[13px] font-medium transition-colors"
                  style={{ color: "var(--color-danger-600)" }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--color-danger-50)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <HiOutlineArrowRightOnRectangle className="w-4 h-4" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
