"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      router.push(isAuthenticated ? "/dashboard" : "/login");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="loading-page">
      <div className="text-center">
        <div className="spinner mx-auto mb-4" />
        <p className="text-sm text-[var(--gray-500)]">Redirecting...</p>
      </div>
    </div>
  );
}
