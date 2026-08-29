"use client";

import { useEffect, useState } from "react";
import api from "@/lib/api";
import type { Profile, PaginatedResponse } from "@/lib/types";
import { HiOutlineUsers, HiOutlineMagnifyingGlass } from "react-icons/hi2";

export default function UsersPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");

  useEffect(() => {
    const params: any = {};
    if (search) params.search = search;
    if (roleFilter) params.role = roleFilter;
    api.get<PaginatedResponse<Profile>>("/accounts/profiles/", { params })
      .then((r) => setProfiles(r.data.results)).catch(console.error).finally(() => setLoading(false));
  }, [search, roleFilter]);

  const roleBadge: Record<string, string> = { student: "badge-primary", instructor: "badge-info", admin: "badge-danger" };

  return (
    <div className="max-w-[1100px] mx-auto space-y-5">
      <div className="page-header"><h1>Users</h1><p>Manage system users and profiles</p></div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <HiOutlineMagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-gray-400)]" />
          <input type="text" placeholder="Search users..." className="input pl-10" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <select className="input select w-auto" style={{ width: "auto", minWidth: "140px" }} value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
          <option value="">All Roles</option>
          <option value="student">Students</option>
          <option value="instructor">Instructors</option>
          <option value="admin">Admins</option>
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      ) : profiles.length === 0 ? (
        <div className="empty-state py-20"><HiOutlineUsers className="empty-state-icon" /><h3>No users found</h3></div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr><th>User</th><th>Email</th><th>Role</th><th>Phone</th><th>Department</th><th>Status</th></tr>
            </thead>
            <tbody>
              {profiles.map((p) => (
                <tr key={p.id}>
                  <td>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-[11px] font-bold flex-shrink-0" style={{ background: "var(--color-gray-900)" }}>
                        {p.full_name?.charAt(0) || "?"}
                      </div>
                      <span className="font-semibold text-[var(--color-gray-900)]">{p.full_name}</span>
                    </div>
                  </td>
                  <td>{p.email}</td>
                  <td><span className={`badge ${roleBadge[p.role] || "badge-gray"}`}>{p.role}</span></td>
                  <td>{p.phone_number || "—"}</td>
                  <td>{p.department_name || "—"}</td>
                  <td><span className={`badge ${p.is_active ? "badge-success" : "badge-gray"}`}>{p.is_active ? "Active" : "Inactive"}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
