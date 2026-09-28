import React from "react";
import { LucideIcon, Inbox } from "lucide-react";
import { Button } from "@/components/ui/Button";

export interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  className?: string;
  testId?: string;
}

export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  actionText,
  onAction,
  className,
  testId,
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center rounded-xl border border-dashed border-white/10 bg-[#0D1117]/60 ${
        className || ""
      }`}
      data-testid={testId}
    >
      <div className="rounded-full bg-[#151B24] border border-white/10 p-3.5 text-[#FF7A18] mb-3">
        <Icon className="h-6 w-6" />
      </div>
      <h4 className="font-display text-sm font-semibold text-[#F5F7FA]">
        {title}
      </h4>
      <p className="mt-1 text-xs text-[#A7AFBD] max-w-sm">
        {description}
      </p>
      {actionText && onAction && (
        <Button
          size="sm"
          variant="outline"
          onClick={onAction}
          className="mt-4 text-xs"
        >
          {actionText}
        </Button>
      )}
    </div>
  );
}
