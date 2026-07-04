"use client";

import { animate, useMotionValue, useMotionValueEvent } from "framer-motion";
import { useEffect, useState } from "react";

interface CompletenessRingProps {
  percentage: number;
  size?: number;
  strokeWidth?: number;
}

export function CompletenessRing({
  percentage,
  size = 160,
  strokeWidth = 10,
}: CompletenessRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  const progress = useMotionValue(0);
  const [displayPercent, setDisplayPercent] = useState(0);
  const [strokeOffset, setStrokeOffset] = useState(circumference);

  useMotionValueEvent(progress, "change", (latest) => {
    const rounded = Math.round(latest);
    setDisplayPercent(rounded);
    setStrokeOffset(circumference - (latest / 100) * circumference);
  });

  useEffect(() => {
    const controls = animate(progress, percentage, {
      duration: 1.5,
      ease: "easeOut",
    });
    return controls.stop;
  }, [percentage, progress]);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={strokeWidth}
          />
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#8b5cf6"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeOffset}
            style={{ transition: "stroke-dashoffset 0.05s linear" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold text-white">{displayPercent}%</span>
        </div>
      </div>
      <p className="text-sm font-medium text-primary">{displayPercent}% Complete</p>
    </div>
  );
}
