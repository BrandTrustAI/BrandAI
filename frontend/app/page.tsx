'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { AdGenerationForm } from '@/components/AdGenerationForm';
import { StatusTracker } from '@/components/StatusTracker';
import { ResultDisplay } from '@/components/ResultDisplay';

export default function Home() {
  const [runId, setRunId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [result, setResult] = useState<any>(null);

  return (
    <div className="min-h-screen bg-white">
      {/* Swiss Design Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
            >
              <h1 className="text-4xl font-bold tracking-tight text-gray-900 mb-2">
                BrandAI
              </h1>
              <p className="text-xs text-gray-500 font-medium tracking-[0.15em] uppercase">
                AI Critique Engine for Generated Ads
              </p>
            </motion.div>
          </div>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="space-y-12"
        >
          {/* Generation Form */}
          {!runId && (
            <AdGenerationForm
              onGenerate={(id) => {
                setRunId(id);
                setStatus(null);
                setResult(null);
              }}
            />
          )}

          {/* Status Tracker - Removed as requested */}

          {/* Result Display */}
          {result && (
            <ResultDisplay result={result} onReset={() => {
              setRunId(null);
              setStatus(null);
              setResult(null);
            }} />
          )}
        </motion.div>
      </main>
    </div>
  );
}
