import React from 'react';

export interface AppError {
  message: string;
  source?: string;
  details?: any;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: AppError;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: AppError; onReset: () => void }>;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error: {
        message: error.message,
        source: 'React Error Boundary',
        details: error.stack
      }
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Send to main process for logging
    try {
      (window as any).api?.send('debug:log', 'react-error', {
        message: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack
      });
    } catch {
      // Ignore if API not available
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return <FallbackComponent error={this.state.error} onReset={this.handleReset} />;
    }

    return this.props.children;
  }
}

const DefaultErrorFallback: React.FC<{ error: AppError; onReset: () => void }> = ({ 
  error, 
  onReset 
}) => (
  <div style={{
    padding: '20px',
    margin: '20px',
    border: '1px solid #ff6b6b',
    borderRadius: '4px',
    backgroundColor: '#fff5f5'
  }}>
    <h2 style={{ color: '#c92a2a', margin: '0 0 10px 0' }}>Something went wrong</h2>
    <p style={{ margin: '0 0 10px 0' }}>{error.message}</p>
    {error.details && (
      <details style={{ marginBottom: '10px' }}>
        <summary>Technical Details</summary>
        <pre style={{ fontSize: '12px', overflow: 'auto' }}>{error.details}</pre>
      </details>
    )}
    <button onClick={onReset} style={{ padding: '8px 16px' }}>
      Try Again
    </button>
  </div>
);