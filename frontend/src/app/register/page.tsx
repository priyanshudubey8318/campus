import React, { Suspense } from "react";
import { RegisterForm } from "@/components/auth/RegisterForm";
import { RingBackground } from "@/components/ui/RingBackground";
import { Loader2 } from "lucide-react";

export default function RegisterPage() {
  return (
    <div className="relative flex min-h-[75vh] items-center justify-center py-8">
      <RingBackground variant="subtle" glowPosition="center" />
      <div className="relative z-10 w-full max-w-lg px-4">
        <Suspense
          fallback={
            <div className="flex justify-center p-8">
              <Loader2 className="h-8 w-8 animate-spin text-[#FF7A18]" />
            </div>
          }
        >
          <RegisterForm />
        </Suspense>
      </div>
    </div>
  );
}
