'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RotateCcw } from 'lucide-react';

interface ResultDisplayProps {
  result: any;
  onReset: () => void;
}

export function ResultDisplay({ result, onReset }: ResultDisplayProps) {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const getMediaUrl = (filePath: string) => {
    if (!filePath) return '';
    
    // Backend returns paths like "ads/{run_id}/var_1.png"
    // Ensure it starts with / for the API call
    let path = filePath.trim();
    
    // Remove any absolute path prefixes
    if (path.startsWith('/app/data/storage/')) {
      path = path.replace('/app/data/storage/', '');
    }
    if (path.startsWith('data/storage/')) {
      path = path.replace('data/storage/', '');
    }
    
    // Ensure path starts with / for API
    if (!path.startsWith('/')) {
      path = '/' + path;
    }
    
    const url = `${API_BASE_URL}/api/v1/media${path}`;
    console.log('Media URL:', url, 'from path:', filePath);
    return url;
  };

  // Debug: Log result to see what we're getting
  console.log('ResultDisplay - result:', result);
  console.log('ResultDisplay - variations:', result?.variations);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="space-y-6"
    >
      {/* Success Message - Removed as requested */}
      
      {/* Generated Media - Removed as requested */}

      {/* Critique Report */}
      {result.critique_report && (
        <Card className="border-gray-200 shadow-none">
          <CardHeader className="pb-6">
            <CardTitle className="text-2xl font-semibold tracking-tight text-gray-900">
              Critique Report
            </CardTitle>
            <CardDescription className="text-sm text-gray-500 mt-2">
              AI-powered analysis and feedback
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 border border-gray-200 rounded-lg">
                  <p className="text-xs text-gray-500 mb-1">Total Variations</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {result.critique_report.total_variations}
                  </p>
                </div>
                <div className="p-4 border border-gray-200 rounded-lg">
                  <p className="text-xs text-gray-500 mb-1">Passed</p>
                  <p className="text-2xl font-semibold text-green-600">
                    {result.critique_report.passed_variations}
                  </p>
                </div>
              </div>

              {result.critique_report.best_variation && (
                <div className="p-6 border border-gray-200 rounded-lg space-y-4">
                  <p className="text-sm font-semibold text-gray-900">Best Variation</p>
                  <div className="space-y-3">
                    {result.critique_report.best_variation.scorecard?.map((score: any, idx: number) => (
                      <div key={idx} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900 capitalize">
                            {score.dimension.replace('_', ' ')}
                          </p>
                          <p className="text-sm font-semibold text-gray-900">
                            {(score.score * 100).toFixed(0)}%
                          </p>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${score.score * 100}%` }}
                            transition={{ duration: 0.6, delay: idx * 0.1 }}
                            className="h-full bg-gray-900"
                          />
                        </div>
                        {score.feedback && (
                          <p className="text-xs text-gray-600 mt-1">{score.feedback}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Reset Button */}
      <div className="flex justify-center pt-6">
        <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
          <Button
            onClick={onReset}
            className="bg-gray-900 text-white hover:bg-gray-800 h-12 px-8 text-sm font-medium tracking-wide uppercase"
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            Generate New Advertisement
          </Button>
        </motion.div>
      </div>
    </motion.div>
  );
}

