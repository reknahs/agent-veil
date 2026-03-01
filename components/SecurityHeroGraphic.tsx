"use client";

import React from "react";

/**
 * Security-themed hero graphic for the landing page.
 * Shield + checkmark (protection/fixed), browser frame, and floating orbs
 * to convey "secure your website" / AgentVeil.
 */
export function SecurityHeroGraphic() {
  return (
    <div className="hero-graphic" aria-hidden>
      {/* Blur orbs (HooBank-style atmosphere) */}
      <div className="hero-graphic-orb hero-graphic-orb-1" />
      <div className="hero-graphic-orb hero-graphic-orb-2" />
      <div className="hero-graphic-orb hero-graphic-orb-3" />

      <svg
        className="hero-graphic-svg"
        viewBox="0 0 400 360"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Browser window frame (glass) */}
        <g filter="url(#browser-shadow)">
          <rect
            x="40"
            y="20"
            width="320"
            height="260"
            rx="12"
            fill="url(#browser-fill)"
            fillOpacity="0.4"
            stroke="rgba(255,255,255,0.12)"
            strokeWidth="1"
          />
          <rect
            x="40"
            y="20"
            width="320"
            height="32"
            rx="12"
            fill="rgba(255,255,255,0.06)"
          />
          <circle cx="68" cy="36" r="4" fill="rgba(255,255,255,0.2)" />
          <circle cx="84" cy="36" r="4" fill="rgba(255,255,255,0.15)" />
          <circle cx="100" cy="36" r="4" fill="rgba(255,255,255,0.1)" />
        </g>

        {/* Shield (center) */}
        <g transform="translate(200 130)">
          <defs>
            <linearGradient id="shield-grad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#22c55e" stopOpacity="0.9" />
              <stop offset="50%" stopColor="#16a34a" stopOpacity="0.95" />
              <stop offset="100%" stopColor="#15803d" stopOpacity="0.9" />
            </linearGradient>
            <linearGradient id="shield-border" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#5eead4" />
              <stop offset="100%" stopColor="#2dd4bf" />
            </linearGradient>
          </defs>
          <path
            d="M0 -70 L55 -35 L55 25 Q55 75 0 95 Q-55 75 -55 25 L-55 -35 Z"
            fill="url(#shield-grad)"
            stroke="url(#shield-border)"
            strokeWidth="2"
            strokeOpacity="0.8"
          />
          {/* Checkmark */}
          <path
            d="M-22 10 L-5 28 L28 -15"
            stroke="white"
            strokeWidth="8"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </g>

        {/* Floating small orbs (data/nodes feel) */}
        <circle cx="80" cy="280" r="20" fill="url(#orb-teal)" fillOpacity="0.6" />
        <circle cx="320" cy="80" r="16" fill="url(#orb-teal)" fillOpacity="0.5" />
        <circle cx="320" cy="300" r="12" fill="url(#orb-green)" fillOpacity="0.5" />
        <circle cx="60" cy="100" r="10" fill="url(#orb-green)" fillOpacity="0.4" />

        <defs>
          <linearGradient id="browser-fill" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#0f172a" />
            <stop offset="100%" stopColor="#020617" />
          </linearGradient>
          <linearGradient id="orb-teal" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#5eead4" />
            <stop offset="100%" stopColor="#2dd4bf" />
          </linearGradient>
          <linearGradient id="orb-green" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="100%" stopColor="#16a34a" />
          </linearGradient>
          <filter id="browser-shadow" x="-20" y="-20" width="440" height="340">
            <feDropShadow dx="0" dy="8" stdDeviation="16" floodOpacity="0.25" />
          </filter>
        </defs>
      </svg>
    </div>
  );
}
