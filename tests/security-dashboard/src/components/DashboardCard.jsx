import React, { useEffect, useRef } from 'react';
import gsap from 'gsap';

export default function DashboardCard({ children, color = 'blue', className = '', isRedAlert = false }) {
  const cardRef = useRef(null);

  const activeColor = isRedAlert ? 'red' : color;

  useEffect(() => {
    if (!cardRef.current) return;

    const glowColor =
      activeColor === 'red'
        ? 'rgba(220,38,38,0.6)'
        : activeColor === 'yellow'
          ? 'rgba(234,179,8,0.55)'
          : 'rgba(6,182,212,0.55)';

    const ctx = gsap.context(() => {
      gsap.to(cardRef.current, {
        boxShadow: isRedAlert
          ? '0 0 50px rgba(220,38,38,0.9)'
          : `0 0 25px ${glowColor}`,
        duration: 0.1,
        repeat: -1,
        yoyo: true,
        ease: isRedAlert
          ? 'rough({ strength: 3, points: 50, randomize: true })'
          : 'rough({ strength: 1, points: 20, randomize: true })',
        repeatDelay: isRedAlert ? 0 : gsap.utils.random(2, 6),
      });
    }, cardRef);

    return () => ctx.revert();
  }, [activeColor, isRedAlert]);

  return (
    <div
      ref={cardRef}
      className={className ? `st-card st-card--${activeColor} ${className}` : `st-card st-card--${activeColor}`}
    >
      {children}
    </div>
  );
}
