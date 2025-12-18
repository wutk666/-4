import { useLayoutEffect } from 'react';
import gsap from 'gsap';
import { RoughEase } from 'gsap/EasePack';

gsap.registerPlugin(RoughEase);

export const useTelekinesis = (ref, intensity = 1) => {
  useLayoutEffect(() => {
    if (!ref.current) return;

    const ctx = gsap.context(() => {
      gsap.to(ref.current, {
        y: `-=${10 * intensity}`,
        rotation: `+=${2 * intensity}`,
        duration: gsap.utils.random(2, 4),
        ease: 'sine.inOut',
        repeat: -1,
        yoyo: true,
        delay: gsap.utils.random(0, 2),
      });
    }, ref);

    return () => ctx.revert();
  }, [ref, intensity]);
};

export const useGlitchTitle = (ref) => {
  useLayoutEffect(() => {
    if (!ref.current) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ repeat: -1, repeatDelay: 5 });
      tl.to(ref.current, {
        textShadow: '4px 0 #ff0000, -4px 0 #0000ff',
        skewX: 20,
        x: -2,
        opacity: 0.82,
        duration: 0.08,
        ease: 'steps(1)',
      })
        .to(ref.current, {
          textShadow: '0px 0 transparent, 0px 0 transparent',
          skewX: 0,
          x: 0,
          opacity: 1,
          duration: 0.1,
        })
        .to(ref.current, {
          textShadow: '2px 0 #ff0000, -2px 0 #0000ff',
          skewX: -16,
          x: 2,
          opacity: 0.86,
          duration: 0.06,
          ease: 'steps(1)',
        })
        .to(ref.current, {
          textShadow: '0px 0 transparent, 0px 0 transparent',
          skewX: 0,
          x: 0,
          opacity: 1,
          duration: 0.1,
        });
    }, ref);

    return () => ctx.revert();
  }, [ref]);
};

export const useNeonFault = (ref, accent = 'rgba(255,0,0,0.35)') => {
  useLayoutEffect(() => {
    if (!ref.current) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ repeat: -1, repeatDelay: gsap.utils.random(2.2, 5.5) });

      tl.to(ref.current, {
        boxShadow: `0 22px 70px rgba(0,0,0,0.55), 0 0 45px ${accent}`,
        filter: 'saturate(1.2) brightness(1.08)',
        duration: 0.12,
        ease: 'steps(1)',
      })
        .to(ref.current, {
          boxShadow: '0 10px 30px rgba(0,0,0,0.18)',
          filter: 'saturate(1) brightness(1)',
          duration: 0.06,
          ease: 'steps(1)',
        })
        .to(ref.current, {
          boxShadow: `0 18px 55px rgba(0,0,0,0.45), 0 0 35px ${accent}`,
          filter: 'saturate(1.15) brightness(1.06)',
          duration: 0.1,
          ease: 'steps(1)',
        })
        .to(ref.current, {
          boxShadow: '0 10px 30px rgba(0,0,0,0.18)',
          filter: 'saturate(1) brightness(1)',
          duration: 0.08,
          ease: 'steps(1)',
        });
    }, ref);

    return () => ctx.revert();
  }, [ref, accent]);
};
