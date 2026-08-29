"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
  HiOutlineHome,
  HiOutlineAcademicCap,
  HiOutlineClipboard,
  HiOutlineCheckCircle,
  HiOutlineMegaphone,
  HiOutlineUser,
  HiOutlineCog6Tooth,
  HiOutlineXMark,
} from "react-icons/hi2";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

interface MenuItem {
  label: string;
  href: string;
  icon: any;
  external?: boolean;
}

const studentMenu: MenuItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: HiOutlineHome },
  { label: "My Courses", href: "/courses", icon: HiOutlineAcademicCap },
  { label: "Assignments", href: "/assignments", icon: HiOutlineClipboard },
  { label: "Attendance", href: "/attendance", icon: HiOutlineCheckCircle },
  { label: "Announcements", href: "/announcements", icon: HiOutlineMegaphone },
];

const instructorMenu: MenuItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: HiOutlineHome },
  { label: "Courses", href: "/courses", icon: HiOutlineAcademicCap },
  { label: "Assignments", href: "/assignments", icon: HiOutlineClipboard },
  { label: "Attendance", href: "/attendance", icon: HiOutlineCheckCircle },
  { label: "Announcements", href: "/announcements", icon: HiOutlineMegaphone },
];

const adminMenu: MenuItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: HiOutlineHome },
  { label: "Courses", href: "/courses", icon: HiOutlineAcademicCap },
  { label: "Assignments", href: "/assignments", icon: HiOutlineClipboard },
  { label: "Attendance", href: "/attendance", icon: HiOutlineCheckCircle },
  { label: "Announcements", href: "/announcements", icon: HiOutlineMegaphone },
  { label: "Users", href: "/users", icon: HiOutlineUser },
  { label: "Admin Panel", href: "http://127.0.0.1:8000/admin/", icon: HiOutlineCog6Tooth, external: true },
];

const roleColors: Record<string, { bg: string; text: string }> = {
  student: { bg: "var(--color-primary-50)", text: "var(--color-primary-700)" },
  instructor: { bg: "var(--color-info-50)", text: "var(--color-info-700)" },
  admin: { bg: "var(--color-danger-50)", text: "var(--color-danger-700)" },
};

export default function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { profile } = useAuth();
  const role = profile?.role || "student";
  const menu = role === "admin" ? adminMenu : role === "instructor" ? instructorMenu : studentMenu;
  const rc = roleColors[role] || roleColors.student;

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/30 backdrop-blur-[2px] z-40 lg:hidden"
          onClick={onClose}
          style={{ transition: "opacity var(--duration-normal)" }}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full bg-white border-r border-[var(--color-gray-200)] flex flex-col transition-transform duration-300 ease-out lg:translate-x-0 lg:static lg:z-auto ${
          open ? "w-[260px] translate-x-0" : "w-[260px] -translate-x-full lg:translate-x-0"
        }`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-5 border-b border-[var(--color-gray-100)]">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-[10px] bg-[var(--color-gray-900)] flex items-center justify-center">
              <span className="text-white font-bold text-sm leading-none">L</span>
            </div>
            <span className="text-[15px] font-bold text-[var(--color-gray-900)] tracking-tight">
              School<span className="text-[var(--color-primary-600)]">LMS</span>
            </span>
          </Link>
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-[var(--radius-sm)] hover:bg-[var(--color-gray-100)] transition-colors"
          >
            <HiOutlineXMark className="w-4 h-4 text-[var(--color-gray-500)]" />
          </button>
        </div>

        {/* Role badge */}
        <div className="px-5 pt-4 pb-2">
          <span
            className="badge"
            style={{ background: rc.bg, color: rc.text }}
          >
            {role.charAt(0).toUpperCase() + role.slice(1)}
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-2 space-y-0.5 overflow-y-auto">
          {menu.map((item) => {
            const isActive =
              item.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(item.href);
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                target={item.external ? "_blank" : undefined}
                onClick={onClose}
                className="flex items-center gap-3 px-3 py-2 rounded-[var(--radius-sm)] text-[13px] font-medium transition-all duration-100"
                style={{
                  background: isActive ? "var(--color-gray-50)" : "transparent",
                  color: isActive ? "var(--color-gray-900)" : "var(--color-gray-500)",
                  fontWeight: isActive ? 600 : 500,
                }}
              >
                <Icon
                  className="w-[18px] h-[18px] flex-shrink-0"
                  style={{ color: isActive ? "var(--color-primary-600)" : "var(--color-gray-400)" }}
                />
                {item.label}
                {item.external && (
                  <svg
                    className="w-3 h-3 ml-auto opacity-30"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Profile */}
        <div className="p-3 border-t border-[var(--color-gray-100)]">
          <Link
            href="/profile"
            onClick={onClose}
            className="flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-sm)] hover:bg-[var(--color-gray-50)] transition-colors"
          >
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
              style={{
                background: `linear-gradient(135deg, var(--color-primary-400), var(--color-primary-600))`,
              }}
            >
              {profile?.full_name?.charAt(0) || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[13px] font-semibold text-[var(--color-gray-900)] truncate leading-tight">
                {profile?.full_name || "User"}
              </p>
              <p className="text-[11px] text-[var(--color-gray-400)] truncate capitalize">
                {role}
              </p>
            </div>
          </Link>
        </div>
      </aside>
    </>
  );
}
