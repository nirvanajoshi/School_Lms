"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import toast from "react-hot-toast";
import { HiOutlineEye, HiOutlineEyeSlash } from "react-icons/hi2";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const router = useRouter();

  if (isAuthenticated) {
    router.push("/dashboard");
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(username, password);
      toast.success("Welcome back!");
      router.push("/dashboard");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left — Branding */}
      <div
        className="hidden lg:flex lg:w-[55%] relative overflow-hidden"
        style={{
          background: "linear-gradient(160deg, #0f172a 0%, #1e293b 50%, #334155 100%)",
        }}
      >
        {/* Decorative shapes */}
        <div className="absolute inset-0 overflow-hidden">
          <div
            className="absolute -top-32 -right-32 w-[500px] h-[500px] rounded-full opacity-[0.04]"
            style={{ background: "white" }}
          />
          <div
            className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full opacity-[0.03]"
            style={{ background: "white" }}
          />
          {/* Grid pattern */}
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage:
                "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
              backgroundSize: "40px 40px",
            }}
          />
        </div>

        <div className="relative z-10 flex flex-col justify-center px-16 xl:px-20">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-12">
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: "rgba(255,255,255,0.1)" }}
            >
              <span className="text-white font-bold text-lg">L</span>
            </div>
            <span className="text-lg font-bold text-white tracking-tight">
              SchoolLMS
            </span>
          </div>

          <h1 className="text-[40px] font-bold text-white leading-[1.15] tracking-tight mb-5 max-w-lg">
            Your learning,
            <br />
            <span style={{ color: "var(--color-primary-400)" }}>simplified.</span>
          </h1>
          <p className="text-[15px] leading-relaxed max-w-md" style={{ color: "rgba(255,255,255,0.6)" }}>
            Access courses, submit assignments, track attendance, and stay informed — all from one place.
          </p>

          {/* Stats */}
          <div className="mt-14 grid grid-cols-3 gap-4 max-w-md">
            {[
              { value: "50+", label: "Courses" },
              { value: "500+", label: "Students" },
              { value: "24/7", label: "Access" },
            ].map((s) => (
              <div
                key={s.label}
                className="p-4 rounded-xl"
                style={{ background: "rgba(255,255,255,0.06)" }}
              >
                <p className="text-2xl font-bold text-white">{s.value}</p>
                <p className="text-[12px] mt-0.5" style={{ color: "rgba(255,255,255,0.5)" }}>
                  {s.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right — Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-white">
        <div className="w-full max-w-[380px]">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2.5 mb-10">
            <div className="w-9 h-9 rounded-[10px] bg-[var(--color-gray-900)] flex items-center justify-center">
              <span className="text-white font-bold text-sm">L</span>
            </div>
            <span className="text-[15px] font-bold text-[var(--color-gray-900)]">
              School<span className="text-[var(--color-primary-600)]">LMS</span>
            </span>
          </div>

          <div className="mb-8">
            <h2 className="text-[22px] font-bold text-[var(--color-gray-900)] tracking-tight">
              Welcome back
            </h2>
            <p className="text-[13px] text-[var(--color-gray-500)] mt-1.5">
              Enter your credentials to access your account
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">
                Username
              </label>
              <input
                type="text"
                className="input"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div>
              <label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  className="input pr-10"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-gray-400)] hover:text-[var(--color-gray-600)] transition-colors"
                >
                  {showPassword ? <HiOutlineEyeSlash className="w-[18px] h-[18px]" /> : <HiOutlineEye className="w-[18px] h-[18px]" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn btn-primary w-full btn-lg"
              style={{ marginTop: "8px" }}
            >
              {loading ? <div className="spinner" style={{ borderTopColor: "white" }} /> : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-center text-[13px] text-[var(--color-gray-500)]">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="font-semibold transition-colors"
              style={{ color: "var(--color-primary-600)" }}
            >
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
