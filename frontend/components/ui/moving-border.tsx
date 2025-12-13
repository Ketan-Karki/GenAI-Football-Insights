"use client";

import React, { useRef } from "react";
import { cn } from "@/lib/utils";

export const MovingBorder = ({
  children,
  duration = 2000,
  className,
  containerClassName,
  borderClassName,
  as: Component = "button",
  ...otherProps
}: {
  children: React.ReactNode;
  duration?: number;
  className?: string;
  containerClassName?: string;
  borderClassName?: string;
  as?: React.ElementType;
  [key: string]: unknown;
}) => {
  return (
    <Component
      className={cn(
        "relative text-xl p-[1px] overflow-hidden",
        containerClassName
      )}
      {...otherProps}
    >
      <div
        className={cn("absolute inset-0", borderClassName)}
        style={{
          background: `linear-gradient(90deg, transparent, #10b981, transparent)`,
          animation: `moveBorder ${duration}ms linear infinite`,
        }}
      />
      <div
        className={cn(
          "relative bg-slate-900/90 backdrop-blur-xl rounded-lg",
          className
        )}
      >
        {children}
      </div>
    </Component>
  );
};
