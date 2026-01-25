import { useEffect, useState } from 'react';

interface PerformanceMetrics {
  renderTime: number;
  memoryUsage?: number;
  connectionLatency: number;
}

export function usePerformanceMonitor() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    renderTime: 0,
    connectionLatency: 0
  });

  useEffect(() => {
    const startTime = performance.now();

    // Measure render time
    const measureRenderTime = () => {
      const endTime = performance.now();
      setMetrics(prev => ({
        ...prev,
        renderTime: endTime - startTime
      }));
    };

    // Measure memory usage if available
    const measureMemoryUsage = () => {
      if ('memory' in performance) {
        const memory = (performance as any).memory;
        setMetrics(prev => ({
          ...prev,
          memoryUsage: memory.usedJSHeapSize / 1024 / 1024 // Convert to MB
        }));
      }
    };

    // Measure connection latency
    const measureLatency = async () => {
      const start = performance.now();
      try {
        await fetch('/api/v1/health', { method: 'HEAD' });
        const end = performance.now();
        setMetrics(prev => ({
          ...prev,
          connectionLatency: end - start
        }));
      } catch (error) {
        // Handle error silently
      }
    };

    measureRenderTime();
    measureMemoryUsage();
    measureLatency();

    // Update metrics periodically
    const interval = setInterval(() => {
      measureMemoryUsage();
      measureLatency();
    }, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, []);

  return metrics;
}