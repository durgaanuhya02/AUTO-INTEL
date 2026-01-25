export const dashboardConfig = {
  // Update intervals (in milliseconds)
  updateIntervals: {
    dashboard: 30000,      // 30 seconds
    websocket: 1000,       // 1 second
    health: 60000,         // 1 minute
  },

  // Chart configurations
  charts: {
    defaultHeight: 200,
    colors: {
      primary: '#3b82f6',
      success: '#10b981',
      warning: '#f59e0b',
      danger: '#ef4444',
    },
    animations: {
      duration: 300,
      easing: 'ease-out',
    },
  },

  // Notification settings
  notifications: {
    defaultDuration: 5000,
    maxVisible: 5,
    position: 'top-right',
  },

  // Performance thresholds
  performance: {
    slowRenderThreshold: 100,    // ms
    highMemoryThreshold: 100,    // MB
    slowConnectionThreshold: 1000, // ms
  },

  // Feature flags
  features: {
    keyboardShortcuts: true,
    performanceMonitoring: true,
    darkMode: false,
    exportData: true,
    realTimeUpdates: true,
  },

  // API configuration
  api: {
    retryAttempts: 3,
    retryDelay: 1000,
    timeout: 10000,
  },

  // UI preferences
  ui: {
    compactMode: false,
    showTooltips: true,
    animationsEnabled: true,
    soundEnabled: false,
  },
};

export type DashboardConfig = typeof dashboardConfig;