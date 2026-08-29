"use client";

import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { HiOutlineUser, HiOutlineKey, HiOutlineCheckCircle } from "react-icons/hi2";

export default function ProfilePage() {
  const { user, profile, refreshProfile } = useAuth();
  const [tab, setTab] = useState<"profile" | "password">("profile");
  const [loading, setLoading] = useState(false);
  const [firstName, setFirstName] = useState(user?.first_name || "");
  const [lastName, setLastName] = useState(user?.last_name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [phone, setPhone] = useState(profile?.phone_number || "");
  const [address, setAddress] = useState(profile?.address || "");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.patch("/accounts/users/me/", { first_name: firstName, last_name: lastName, email });
      await api.patch("/accounts/profiles/me/", { phone_number: phone, address });
      await refreshProfile();
      toast.success("Profile updated!");
    } catch (err: any) { toast.error(err.response?.data?.detail || "Failed"); }
    finally { setLoading(false); }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) { toast.error("Passwords don't match"); return; }
    setLoading(true);
    try {
      await api.post("/accounts/auth/change-password/", { old_password: oldPassword, new_password: newPassword, new_password_confirm: confirmPassword });
      toast.success("Password changed!");
      setOldPassword(""); setNewPassword(""); setConfirmPassword("");
    } catch (err: any) {
      const d = err.response?.data;
      toast.error(d?.old_password?.[0] || d?.new_password?.[0] || d?.detail || "Failed");
    } finally { setLoading(false); }
  };

  return (
    <div className="max-w-[640px] mx-auto space-y-5">
      <div className="page-header"><h1>Profile & Settings</h1><p>Manage your account information</p></div>

      <div className="card p-6">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6 pb-6" style={{ borderBottom: "1px solid var(--color-gray-100)" }}>
          <div className="w-14 h-14 rounded-[var(--radius-lg)] flex items-center justify-center text-white text-xl font-bold flex-shrink-0" style={{ background: "linear-gradient(135deg, var(--color-primary-400), var(--color-primary-600))" }}>
            {profile?.full_name?.charAt(0) || "U"}
          </div>
          <div>
            <h2 className="text-[18px] font-bold text-[var(--color-gray-900)]">{profile?.full_name || user?.username}</h2>
            <p className="text-[13px] text-[var(--color-gray-500)]">{user?.email}</p>
            <span className={`badge mt-1.5 ${profile?.role === "admin" ? "badge-danger" : profile?.role === "instructor" ? "badge-info" : "badge-primary"}`}>
              {profile?.role || "student"}
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs mb-6">
          <button onClick={() => setTab("profile")} className={`tab-btn ${tab === "profile" ? "active" : ""}`}>
            <HiOutlineUser className="w-4 h-4" />Profile
          </button>
          <button onClick={() => setTab("password")} className={`tab-btn ${tab === "password" ? "active" : ""}`}>
            <HiOutlineKey className="w-4 h-4" />Password
          </button>
        </div>

        {tab === "profile" ? (
          <form onSubmit={handleProfileUpdate} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">First Name</label><input type="text" className="input" value={firstName} onChange={(e) => setFirstName(e.target.value)} /></div>
              <div><label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Last Name</label><input type="text" className="input" value={lastName} onChange={(e) => setLastName(e.target.value)} /></div>
            </div>
            <div><label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Email</label><input type="email" className="input" value={email} onChange={(e) => setEmail(e.target.value)} /></div>
            <div><label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Phone</label><input type="tel" className="input" placeholder="+1 (555) 123-4567" value={phone} onChange={(e) => setPhone(e.target.value)} /></div>
            <div><label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Address</label><textarea className="input min-h-[80px] resize-y" value={address} onChange={(e) => setAddress(e.target.value)} /></div>
            <div className="flex justify-end pt-1">
              <button type="submit" disabled={loading} className="btn btn-primary">
                {loading ? <div className="spinner" style={{ borderTopColor: "white" }} /> : <><HiOutlineCheckCircle className="w-4 h-4" />Save</>}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handlePasswordChange} className="space-y-4">
            <div><label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Current Password</label><input type="password" className="input" placeholder="Enter current password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} required /></div>
            <div><label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">New Password</label><input type="password" className="input" placeholder="Min 8 characters" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} /></div>
            <div><label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Confirm New Password</label><input type="password" className="input" placeholder="Repeat new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} /></div>
            <div className="flex justify-end pt-1">
              <button type="submit" disabled={loading} className="btn btn-primary">
                {loading ? <div className="spinner" style={{ borderTopColor: "white" }} /> : <><HiOutlineKey className="w-4 h-4" />Change Password</>}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
