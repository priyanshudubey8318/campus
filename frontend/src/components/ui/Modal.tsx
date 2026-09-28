"use client";

import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl";
}

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  maxWidth = "md",
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = "hidden";
      window.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.body.style.overflow = "unset";
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxWidthClasses = {
    sm: "max-w-sm",
    md: "max-w-md",
    lg: "max-w-lg",
    xl: "max-w-xl",
    "2xl": "max-w-2xl",
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto p-4 bg-[#07090D]/85 backdrop-blur-md transition-opacity flex min-h-full items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      data-testid="modal-backdrop"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={modalRef}
        className={cn(
          "relative w-full max-h-[90vh] overflow-y-auto rounded-2xl border border-white/10 bg-[#151B24] p-6 shadow-[0_20px_60px_rgba(0,0,0,0.8)] transition-all animate-in fade-in-90 zoom-in-95",
          maxWidthClasses[maxWidth]
        )}
      >
        <div className="flex items-start justify-between pb-4 border-b border-white/[0.08]">
          <div>
            <h2
              id="modal-title"
              className="font-display text-lg font-bold tracking-tight text-[#F5F7FA]"
            >
              {title}
            </h2>
            {description && (
              <p className="mt-1 text-xs text-[#A7AFBD]">
                {description}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            data-testid="modal-close-button"
            className="rounded-lg p-1.5 text-[#A7AFBD] hover:bg-white/[0.08] hover:text-[#F5F7FA] transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-4 text-[#F5F7FA]">{children}</div>
      </div>
    </div>
  );
}
