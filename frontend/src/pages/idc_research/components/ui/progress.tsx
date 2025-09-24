"use client";

import * as React from "react";
import * as ProgressPrimitive from "@radix-ui/react-progress";

import { cn } from "./utils";

function Progress({
  className,
  value,
  ...props
}: React.ComponentProps<typeof ProgressPrimitive.Root>) {
  return (
    <ProgressPrimitive.Root
      data-slot="progress"
      className={cn(
        "bg-primary/20 relative h-2 w-full overflow-hidden rounded-full",
        className,
      )}
      style={{ backgroundColor: "var(--color-input-background, var(--input-background))" }}
      {...props}
    >
      <ProgressPrimitive.Indicator
        data-slot="progress-indicator"
        className="bg-primary h-full w-full flex-1 transition-all"
        style={{
          width: `${Math.max(0, Math.min(100, Number(value) || 0))}%`,
          backgroundColor: "var(--color-primary, var(--primary))",
        }}
      />
    </ProgressPrimitive.Root>
  );
}

export { Progress };
