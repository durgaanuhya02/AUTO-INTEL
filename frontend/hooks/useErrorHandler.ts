'use client';

import { useState, useCallback } from 'react';

export interface ErrorInfo {
  message: string;
  code?: string;
  details?: any;
  timestamp: Date;
  context?: string;
}

export function useErrorHandler() {
  const [errors, setErrors] = useState<ErrorInfo[]>([]);

  const handleError = useCallback((error: any, context?: string) => {
    const errorInfo: ErrorInfo = {
      message: error.message || 'An unexpected error occurred',
      code: error.code || error.status?.toString(),
      details: error.details || error.response?.data,
      timestamp: new Date(),
      context
    };

    setErrors(prev => [errorInfo, ...prev.slice(0, 9)]); // Keep last 10 errors

    // Log to console for debugging
    console.error('Error handled:', errorInfo);

    // In production, send to error tracking service
    if (process.env.NODE_ENV === 'production') {
      // sendToErrorTracking(errorInfo);
    }
  }, []);

  const handleApiError = useCallback(async (response: Response, context?: string) => {
    let errorMessage = 'API request failed';
    let errorDetails = null;

    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
      errorDetails = errorData;
    } catch {
      errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    }

    handleError({
      message: errorMessage,
      code: response.status.toString(),
      details: errorDetails
    }, context);
  }, [handleError]);

  const clearErrors = useCallback(() => {
    setErrors([]);
  }, []);

  const retryOperation = useCallback(async (operation: () => Promise<any>, context?: string) => {
    try {
      return await operation();
    } catch (error) {
      handleError(error, context);
      throw error;
    }
  }, [handleError]);

  return {
    errors,
    handleError,
    handleApiError,
    clearErrors,
    retryOperation
  };
}