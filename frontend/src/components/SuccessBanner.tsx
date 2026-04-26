import { useEffect, useState } from 'react';
import { CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SuccessBannerProps {
  totalRegions: number;
  product: string;
  niche: string;
  show: boolean;
}

export function SuccessBanner({ totalRegions, product, niche, show }: SuccessBannerProps) {
  const [visible, setVisible] = useState(show);

  useEffect(() => {
    if (show) {
      setVisible(true);
      const timer = setTimeout(() => setVisible(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [show]);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className="rounded-lg border border-primary/30 bg-primary/10 p-4"
        >
          <div className="flex items-center gap-3">
            <CheckCircle className="h-5 w-5 text-primary shrink-0" />
            <p className="text-sm font-medium">
              <span className="text-primary">{totalRegions} regiões</span> identificadas para{' '}
              <span className="font-semibold">{product}</span> no nicho{' '}
              <span className="font-semibold text-primary">{niche}</span>
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
