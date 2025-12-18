import React, { useRef } from 'react';

import { useTelekinesis } from '../hooks/useGSAPAnimations';

export default function FloatingIcon({ children, intensity = 1, className = '' }) {
  const ref = useRef(null);
  useTelekinesis(ref, intensity);

  return (
    <div ref={ref} className={className ? `floating-icon ${className}` : 'floating-icon'}>
      {children}
    </div>
  );
}
