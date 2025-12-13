"use client";

import React, { useId, useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface SparklesProps {
  id?: string;
  className?: string;
  background?: string;
  minSize?: number;
  maxSize?: number;
  particleDensity?: number;
  particleColor?: string;
  children?: React.ReactNode;
}

export const SparklesCore = ({
  id,
  className,
  background = "transparent",
  minSize = 0.4,
  maxSize = 1,
  particleDensity = 100,
  particleColor = "#FFF",
  children,
}: SparklesProps) => {
  const [particles, setParticles] = useState<
    Array<{
      id: number;
      x: number;
      y: number;
      size: number;
      duration: number;
      delay: number;
    }>
  >([]);

  const generatedId = useId();
  const effectId = id || generatedId;

  useEffect(() => {
    const generateParticles = () => {
      const newParticles = [];
      for (let i = 0; i < particleDensity; i++) {
        newParticles.push({
          id: i,
          x: Math.random() * 100,
          y: Math.random() * 100,
          size: Math.random() * (maxSize - minSize) + minSize,
          duration: Math.random() * 2 + 1,
          delay: Math.random() * 2,
        });
      }
      setParticles(newParticles);
    };

    generateParticles();
  }, [particleDensity, minSize, maxSize]);

  return (
    <div className={cn("relative h-full w-full", className)}>
      <svg className="absolute inset-0 h-full w-full" style={{ background }}>
        {particles.map((particle) => (
          <circle
            key={particle.id}
            cx={`${particle.x}%`}
            cy={`${particle.y}%`}
            r={particle.size}
            fill={particleColor}
            opacity="0"
          >
            <animate
              attributeName="opacity"
              values="0;1;0"
              dur={`${particle.duration}s`}
              begin={`${particle.delay}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))}
      </svg>
      {children}
    </div>
  );
};

export const Sparkles = ({ children, ...props }: SparklesProps) => {
  return (
    <div className="relative">
      <SparklesCore {...props} />
      <div className="relative z-10">{children}</div>
    </div>
  );
};
