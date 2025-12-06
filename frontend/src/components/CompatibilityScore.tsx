import { cn } from "@/lib/utils";
import React, { useState, useEffect } from "react";
import { STYLING } from "./constants";
import { COMPATIBILITY_LABELS } from "./constants";

type CompatibilityScoreProps = {
  score: number;
  className?: string;
};

function getScoreLabel(score: number): string {
  if (score >= 9) return COMPATIBILITY_LABELS.PERFECT_MATCH;
  if (score >= 8) return COMPATIBILITY_LABELS.GREAT_MATCH;
  if (score >= 6) return COMPATIBILITY_LABELS.GOOD_POTENTIAL;
  if (score >= 4) return COMPATIBILITY_LABELS.LOW_COMPATIBILITY;
  return COMPATIBILITY_LABELS.VERY_LOW;
}

export function AnimatedCircularProgressBar({
  max = 10,
  min = 0,
  value = 0,
  gaugePrimaryColor,
  gaugeSecondaryColor,
  className,
  label,
}: {
  max?: number;
  min?: number;
  value?: number;
  gaugePrimaryColor: string;
  gaugeSecondaryColor: string;
  className?: string;
  label?: string;
}) {
  const circumference = 2 * Math.PI * 45;
  const percentPx = circumference / 100;
  const currentPercent = Math.round(((value - min) / (max - min)) * 100);

  return (
    <>
    <div
      className={cn("relative size-40 text-2xl font-semibold flex items-center justify-center", className)}
      style={
        {
          "--circle-size": "100px",
          "--circumference": circumference,
          "--percent-to-px": `${percentPx}px`,
          "--gap-percent": "5",
          "--offset-factor": "0",
          "--transition-length": "1s",
          "--transition-step": "200ms",
          "--delay": "0s",
          "--percent-to-deg": "3.6deg",
          transform: "translateZ(0)",
        } as React.CSSProperties
      }
    >
      <svg
        fill="none"
        className="size-full absolute top-0 left-0"
        strokeWidth="2"
        viewBox="0 0 100 100"
        style={{ zIndex: 1 }}
      >
        {currentPercent <= 90 && currentPercent >= 0 && (
          <circle
            cx="50"
            cy="50"
            r="45"
            strokeWidth="10"
            strokeDashoffset="0"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="opacity-100"
            style={
              {
                stroke: gaugeSecondaryColor,
                "--stroke-percent": 90 - currentPercent,
                "--offset-factor-secondary": "calc(1 - var(--offset-factor))",
                strokeDasharray:
                  "calc(var(--stroke-percent) * var(--percent-to-px)) var(--circumference)",
                transform:
                  "rotate(calc(1turn - 90deg - (var(--gap-percent) * var(--percent-to-deg) * var(--offset-factor-secondary)))) scaleY(-1)",
                transition: "all var(--transition-length) ease var(--delay)",
                transformOrigin:
                  "calc(var(--circle-size) / 2) calc(var(--circle-size) / 2)",
              } as React.CSSProperties
            }
          />
        )}
        <circle
          cx="50"
          cy="50"
          r="45"
          strokeWidth="10"
          strokeDashoffset="0"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="opacity-100"
          style={
            {
              stroke: gaugePrimaryColor,
              "--stroke-percent": currentPercent,
              strokeDasharray:
                "calc(var(--stroke-percent) * var(--percent-to-px)) var(--circumference)",
              transition:
                "var(--transition-length) ease var(--delay),stroke var(--transition-length) ease var(--delay)",
              transitionProperty: "stroke-dasharray,transform",
              transform:
                "rotate(calc(-90deg + var(--gap-percent) * var(--offset-factor) * var(--percent-to-deg)))",
              transformOrigin:
                "calc(var(--circle-size) / 2) calc(var(--circle-size) / 2)",
            } as React.CSSProperties
          }
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center z-10">
        <span
          data-current-value={currentPercent}
          className="text-5xl font-bold leading-none"
        >
          {value}
        </span>
        {/* {label && (
          <span className="mt-2 text-sm font-medium text-gray-700 text-center">
            {label}
          </span>
        )} */}
      </div>
    </div>
    {label && (
      <span style={{ marginTop: STYLING.SPACING.SMALL }} className="mt-2 text-md font-bold text-gray-700 text-center">
        {label}
      </span>
    )}
    </>
  );
}

const CompatibilityScore: React.FC<CompatibilityScoreProps> = ({ score, className }) => {
  const [animatedScore, setAnimatedScore] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimatedScore(score);
    }, 100);
    return () => clearTimeout(timer);
  }, [score]);

  const label = getScoreLabel(animatedScore);

  return (
    <div className="flex flex-col">
      <AnimatedCircularProgressBar
        value={animatedScore}
        gaugePrimaryColor="#020122"
        gaugeSecondaryColor="#6B5E62"
        className={className}
        label={label} 
      />
    </div>
  );
};

export default CompatibilityScore;