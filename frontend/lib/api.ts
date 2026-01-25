const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class ApiClient {
  private baseUrl: string;
  private retryAttempts: number = 3;
  private retryDelay: number = 1000;
  private requestTimeout: number = 30000;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.requestTimeout);
    
    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const response = await fetch(url, {
          headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
          },
          signal: controller.signal,
          ...options,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          let errorData;
          
          try {
            errorData = JSON.parse(errorText);
          } catch {
            errorData = { message: errorText };
          }

          throw new ApiError(
            errorData.detail || errorData.message || `HTTP ${response.status}`,
            response.status,
            errorData,
            url
          );
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          return response.json();
        } else {
          return response.text() as any;
        }
      } catch (error) {
        clearTimeout(timeoutId);
        
        if (error instanceof ApiError) {
          throw error;
        }

        if (error.name === 'AbortError') {
          throw new ApiError('Request timeout', 408, null, url);
        }

        if (attempt === this.retryAttempts) {
          throw new ApiError(
            error.message || 'Network error',
            0,
            { originalError: error },
            url
          );
        }
        
        // Wait before retrying with exponential backoff
        await new Promise(resolve => setTimeout(resolve, this.retryDelay * Math.pow(2, attempt - 1)));
      }
    }
    
    throw new ApiError('Max retry attempts reached', 0, null, url);
  }

  // Dashboard endpoints
  async getDashboardData() {
    return this.request('/dashboard');
  }

  async getMetrics(metricType?: string, hours: number = 24) {
    const params = new URLSearchParams();
    if (metricType) params.append('metric_type', metricType);
    params.append('hours', hours.toString());
    
    return this.request(`/metrics?${params.toString()}`);
  }

  async getAlerts(limit: number = 50) {
    return this.request(`/alerts?limit=${limit}`);
  }

  async getDecisions(limit: number = 20) {
    return this.request(`/decisions?limit=${limit}`);
  }

  // Agent endpoints
  async getAgentStatus() {
    return this.request('/agents/status');
  }

  async triggerAnalysis(metricType: string, currentValue: number, description?: string) {
    return this.request('/agents/trigger', {
      method: 'POST',
      body: JSON.stringify({
        metric_type: metricType,
        current_value: currentValue,
        description,
      }),
    });
  }

  // Approval endpoints
  async getApprovalQueue() {
    return this.request('/approval-queue');
  }

  async approveDecision(
    decisionId: string,
    approved: boolean,
    approver: string,
    comments?: string
  ) {
    return this.request('/approve-decision', {
      method: 'POST',
      body: JSON.stringify({
        decision_id: decisionId,
        approved,
        approver,
        comments,
      }),
    });
  }

  // Insights endpoints
  async getInsights() {
    return this.request('/insights');
  }

  // System health
  async getSystemHealth() {
    return this.request('/system/health');
  }

  async getComprehensiveSystemHealth() {
    return this.request('/system/comprehensive-health');
  }

  // ML endpoints
  async uploadCSV(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    return this.request('/ml/upload-csv', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }

  async trainModel(config: {
    file_path: string;
    target_column: string;
    model_type?: string;
    model_name?: string;
  }) {
    return this.request('/ml/train-model', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  async getModels() {
    return this.request('/ml/models');
  }

  async deleteModel(modelName: string) {
    return this.request(`/ml/models/${modelName}`, {
      method: 'DELETE',
    });
  }

  async makePrediction(modelName: string, data: Record<string, any>) {
    return this.request('/ml/predict', {
      method: 'POST',
      body: JSON.stringify({
        model_name: modelName,
        data,
      }),
    });
  }

  // Analytics endpoints
  async getForecasts() {
    return this.request('/analytics/forecasts');
  }

  async getCustomerSegments() {
    return this.request('/analytics/customer-segments');
  }

  async getAdvancedAnomalies(limit: number = 20) {
    return this.request(`/analytics/anomalies/advanced?limit=${limit}`);
  }

  async getAnalyticsStatus() {
    return this.request('/analytics/status');
  }

  // Enterprise integration endpoints
  async getIntegrationStatus() {
    return this.request('/enterprise/integrations/status');
  }

  async getRealTimeMetrics() {
    return this.request('/metrics/real-time');
  }
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data: any = null,
    public url: string = ''
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export const apiClient = new ApiClient();

// Enhanced WebSocket connection with better error handling
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private listeners: Map<string, ((data: any) => void)[]> = new Map();
  private connectionPromise: Promise<void> | null = null;
  private isConnecting = false;

  constructor(private url: string = 'ws://localhost:8000/ws') {}

  connect(): Promise<void> {
    if (this.connectionPromise && this.isConnecting) {
      return this.connectionPromise;
    }

    this.isConnecting = true;
    this.connectionPromise = new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        const connectionTimeout = setTimeout(() => {
          if (this.ws?.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000);

        this.ws.onopen = () => {
          clearTimeout(connectionTimeout);
          console.log('WebSocket connected');
          this.reconnectAttempts = 0;
          this.isConnecting = false;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          clearTimeout(connectionTimeout);
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.connectionPromise = null;
          
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.attemptReconnect();
          }
        };

        this.ws.onerror = (error) => {
          clearTimeout(connectionTimeout);
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });

    return this.connectionPromise;
  }

  private handleMessage(message: any) {
    const { type, data } = message;
    const typeListeners = this.listeners.get(type) || [];
    const allListeners = this.listeners.get('*') || [];
    
    [...typeListeners, ...allListeners].forEach(listener => {
      try {
        listener(data);
      } catch (error) {
        console.error('Error in WebSocket listener:', error);
      }
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect().catch(error => {
          console.error('Reconnection failed:', error);
        });
      }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1));
    } else {
      console.error('Max reconnection attempts reached');
    }
  }

  on(type: string, listener: (data: any) => void) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type)!.push(listener);
  }

  off(type: string, listener: (data: any) => void) {
    const typeListeners = this.listeners.get(type);
    if (typeListeners) {
      const index = typeListeners.indexOf(listener);
      if (index > -1) {
        typeListeners.splice(index, 1);
      }
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, message not sent:', message);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    this.connectionPromise = null;
    this.isConnecting = false;
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();