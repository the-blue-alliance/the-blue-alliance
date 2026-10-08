import { motion, useReducedMotion } from 'motion/react';

export default function AnimatedTabIndicator() {
  const reduceMotion = useReducedMotion();
  return (
    <motion.span
      layoutId="tab-indicator"
      initial={false}
      className="absolute inset-0 rounded-sm bg-background shadow-xs"
      transition={
        reduceMotion
          ? { duration: 0 }
          : { type: 'spring', bounce: 0.15, duration: 0.4 }
      }
    />
  );
}
