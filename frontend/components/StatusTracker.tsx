'use client';

import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import { getStatus, getResult } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';

interface StatusTrackerProps {
  runId: string;
  onStatusUpdate: (status: any) => void;
  onComplete: (result: any) => void;
}

export function StatusTracker({ runId, onStatusUpdate, onComplete }: StatusTrackerProps) {
  const { data: status, isLoading } = useQuery({
    queryKey: ['status', runId],
    queryFn: () => getStatus(runId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === 'completed' || status === 'failed') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
    // Enable refetch on window focus to keep progress updated
    refetchOnWindowFocus: true,
  });
  
  // Debug: Log status updates
  useEffect(() => {
    if (status) {
      console.log('StatusTracker - Status update:', {
        status: status.status,
        progress: status.progress,
        current_stage: status.current_stage,
      });
    }
  }, [status]);

  useEffect(() => {
    if (status) {
      onStatusUpdate(status);
      
      if (status.status === 'completed') {
        // Fetch final result
        getResult(runId).then(onComplete);
      }
    }
  }, [status, runId, onStatusUpdate, onComplete]);

  if (isLoading || !status) {
    return (
      <Card className="border-gray-200 shadow-none">
        <CardContent className="py-12">
          <div className="flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'processing':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4" />;
      case 'failed':
        return <XCircle className="h-4 w-4" />;
      default:
        return <Loader2 className="h-4 w-4 animate-spin" />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <Card className="border-gray-200 shadow-none">
        <CardHeader className="pb-6">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl font-semibold tracking-tight text-gray-900">
                Generation Status
              </CardTitle>
              <CardDescription className="text-xs text-gray-500 mt-2 font-mono tracking-wide">
                {runId}
              </CardDescription>
            </div>
            <Badge className={getStatusColor(status.status)}>
              <span className="flex items-center gap-2">
                {getStatusIcon(status.status)}
                {status.status}
              </span>
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600 font-medium">Progress</span>
              <span className="text-gray-900 font-semibold">{Math.round(status.progress || 0)}%</span>
            </div>
            <Progress value={status.progress || 0} className="h-2" />
          </div>

          {/* Current Stage */}
          {status.current_stage && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-900">Current Stage</p>
              <p className="text-sm text-gray-600 capitalize">{status.current_stage.replace('_', ' ')}</p>
            </div>
          )}

          {/* Message */}
          {status.message && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-gray-900">Message</p>
              <p className="text-sm text-gray-600">{status.message}</p>
            </div>
          )}

          {/* Timestamps */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
            <div>
              <p className="text-xs text-gray-500 mb-1">Created</p>
              <p className="text-xs text-gray-900">
                {new Date(status.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">Last Updated</p>
              <p className="text-xs text-gray-900">
                {new Date(status.updated_at).toLocaleString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

