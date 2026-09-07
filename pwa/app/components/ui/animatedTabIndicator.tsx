import { motion } from 'motion/react';

export default function AnimatedTabIndicator() {
  return (
    <motion.span
      layoutId="tab-indicator"
      initial={false}
      className="absolute inset-0 rounded-sm bg-background shadow-xs"
      transition={{ type: 'spring', bounce: 0.15, duration: 0.4 }}
    />
  );
}
