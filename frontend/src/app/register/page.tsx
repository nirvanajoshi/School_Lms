"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import toast from "react-hot-toast";
import { HiOutlineEye, HiOutlineEyeSlash } from "react-icons/hi2";

export default function RegisterPage() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    password_confirm: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register, isAuthenticated } = useAuth();
  const router = useRouter();

  if (isAuthenticated) {
    router.push("/dashboard");
    return null;
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password !== form.password_confirm) {
      toast.error("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      await register(form);
      toast.success("Account created! Welcome to School LMS!");
      router.push("/dashboard");
    } catch (err: any) {
      const data = err.response?.data;
      if (data) {
        const msg = typeof data === "object" ? Object.values(data).flat().join(", ") : data;
        toast.error(typeof msg === "string" ? msg : "Registration failed");
      } else {
        toast.error("Registration failed");
      }
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
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-32 -right-32 w-[500px] h-[500px] rounded-full opacity-[0.04]" style={{ background: "white" }} />
          <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full opacity-[0.03]" style={{ background: "white" }} />
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage: "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
              backgroundSize: "40px 40px",
            }}
          />
        </div>

        <div className="relative z-10 flex flex-col justify-center px-16 xl:px-20">
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: "rgba(255,255,255,0.1)" }}>
              <span className="text-white font-bold text-lg">L</span>
            </div>
            <span className="text-lg font-bold text-white tracking-tight">SchoolLMS</span>
          </div>

          <h1 className="text-[40px] font-bold text-white leading-[1.15] tracking-tight mb-5 max-w-lg">
            Start your
            <br />
            <span style={{ color: "var(--color-primary-400)" }}>academic journey.</span>
          </h1>
          <p className="text-[15px] leading-relaxed max-w-md" style={{ color: "rgba(255,255,255,0.6)" }}>
            Join thousands of students and educators using SchoolLMS for a smarter learning experience.
          </p>

          <div className="mt-12 space-y-3 max-w-md">
            {[
              "Access courses and materials anytime",
              "Submit assignments online",
              "Track your attendance in real-time",
              "Stay updated with announcements",
            ].map((item) => (
              <div key={item} className="flex items-center gap-3">
                <div className="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: "var(--color-success-500)" }}>
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-[14px]" style={{ color: "rgba(255,255,255,0.8)" }}>{item}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right — Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-white">
        <div className="w-full max-w-[380px]">
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
              Create your account
            </h2>
            <p className="text-[13px] text-[var(--color-gray-500)] mt-1.5">
              Fill in your details to get started
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3.5">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">First Name</label>
                <input type="text" name="first_name" className="input" placeholder="John" value={form.first_name} onChange={handleChange} required />
              </div>
              <div>
                <label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Last Name</label>
                <input type="text" name="last_name" className="input" placeholder="Doe" value={form.last_name} onChange={handleChange} required />
              </div>
            </div>

            <div>
              <label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Username</label>
              <input type="text" name="username" className="input" placeholder="johndoe" value={form.username} onChange={handleChange} required />
            </div>

            <div>
              <label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Email</label>
              <input type="email" name="email" className="input" placeholder="john@example.com" value={form.email} onChange={handleChange} required />
            </div>

            <div>
              <label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Password</label>
              <div className="relative">
                <input type={showPassword ? "text" : "password"} name="password" className="input pr-10" placeholder="Min 8 characters" value={form.password} onChange={handleChange} required minLength={8} />
                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-gray-400)] hover:text-[var(--color-gray-600)] transition-colors">
                  {showPassword ? <HiOutlineEyeSlash className="w-[18px] h-[18px]" /> : <HiOutlineEye className="w-[18px] h-[18px]" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-[13px] font-semibold text-[var(--color-gray-700)] mb-1.5">Confirm Password</label>
              <input type="password" name="password_confirm" className="input" placeholder="Repeat your password" value={form.password_confirm} onChange={handleChange} required minLength={8} />
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary w-full btn-lg" style={{ marginTop: "12px" }}>
              {loading ? <div className="spinner" style={{ borderTopColor: "white" }} /> : "Create account"}
            </button>
          </form>

          <p className="mt-5 text-center text-[13px] text-[var(--color-gray-500)]">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold transition-colors" style={{ color: "var(--color-primary-600)" }}>
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
