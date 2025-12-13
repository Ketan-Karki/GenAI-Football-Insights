"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";

interface GlitchTextProps {
  text: string;
  className?: string;
}

export function GlitchText({ text, className }: GlitchTextProps) {
  const [isGlitching, setIsGlitching] = useState(false);

  const handleMouseEnter = () => {
    setIsGlitching(true);
    setTimeout(() => setIsGlitching(false), 300);
  };

  return (
    <span
      className={cn(
        "relative inline-block cursor-pointer",
        isGlitching && "animate-glitch",
        className
      )}
      onMouseEnter={handleMouseEnter}
    >
      {text}
      {isGlitching && (
        <>
          <span
            className="absolute top-0 left-0 text-[#FCD535] opacity-70"
            style={{ transform: "translate(-2px, -2px)" }}
          >
            {text}
          </span>
          <span
            className="absolute top-0 left-0 text-[#0ECB81] opacity-70"
            style={{ transform: "translate(2px, 2px)" }}
          >
            {text}
          </span>
        </>
      )}
    </span>
  );
}
