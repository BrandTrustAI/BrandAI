'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { generateAd } from '@/lib/api';
import { useMutation } from '@tanstack/react-query';
import { Upload, Loader2, Sparkles } from 'lucide-react';

interface AdGenerationFormProps {
  onGenerate: (runId: string) => void;
}

export function AdGenerationForm({ onGenerate }: AdGenerationFormProps) {
  const [prompt, setPrompt] = useState('');
  const [mediaType, setMediaType] = useState<'image' | 'video'>('image');
  const [brandUrl, setBrandUrl] = useState('');
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [productFile, setProductFile] = useState<File | null>(null);

  const mutation = useMutation({
    mutationFn: async (formData: FormData) => {
      return await generateAd(formData);
    },
    onSuccess: (data) => {
      onGenerate(data.run_id);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('media_type', mediaType);
    if (brandUrl) formData.append('brand_website_url', brandUrl);
    if (logoFile) formData.append('logo', logoFile);
    if (productFile) formData.append('product', productFile);

    // Debug: Log what we're sending
    console.log('FormData being sent:');
    console.log('  prompt:', prompt);
    console.log('  media_type:', mediaType);
    console.log('  brand_website_url:', brandUrl);
    console.log('  logo:', logoFile?.name);
    console.log('  product:', productFile?.name);
    
    // Log FormData entries
    for (const [key, value] of formData.entries()) {
      if (value instanceof File) {
        console.log(`  ${key}: File(${value.name}, ${value.size} bytes, ${value.type})`);
      } else {
        console.log(`  ${key}: ${typeof value === 'string' ? value.substring(0, 100) : value}`);
      }
    }

    mutation.mutate(formData);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <Card className="border-gray-200 shadow-none hover:shadow-sm transition-shadow duration-300">
        <CardHeader className="pb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Sparkles className="h-5 w-5 text-gray-900" />
            </div>
            <div>
              <CardTitle className="text-2xl font-semibold tracking-tight text-gray-900">
                Generate Advertisement
              </CardTitle>
              <CardDescription className="text-xs text-gray-500 mt-1 tracking-wide">
                Create AI-generated ads with intelligent critique and refinement
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Prompt */}
            <div className="space-y-2">
              <Label htmlFor="prompt" className="text-sm font-medium text-gray-900">
                Advertisement Prompt
              </Label>
              <Textarea
                id="prompt"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your advertisement concept..."
                required
                minLength={10}
                maxLength={1000}
                className="min-h-[120px] resize-none border-gray-300 focus:border-gray-900 focus:ring-gray-900"
              />
              <p className="text-xs text-gray-500">
                {prompt.length}/1000 characters
              </p>
            </div>

            {/* Media Type */}
            <div className="space-y-2">
              <Label htmlFor="media-type" className="text-sm font-medium text-gray-900">
                Media Type
              </Label>
              <Select value={mediaType} onValueChange={(value: 'image' | 'video') => setMediaType(value)}>
                <SelectTrigger id="media-type" className="border-gray-300 focus:border-gray-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="image">Image</SelectItem>
                  <SelectItem value="video">Video</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Brand Website URL */}
            <div className="space-y-2">
              <Label htmlFor="brand-url" className="text-sm font-medium text-gray-900">
                Brand Website URL <span className="text-gray-400 font-normal">(Optional)</span>
              </Label>
              <Input
                id="brand-url"
                type="url"
                value={brandUrl}
                onChange={(e) => setBrandUrl(e.target.value)}
                placeholder="https://example.com"
                className="border-gray-300 focus:border-gray-900 focus:ring-gray-900"
              />
            </div>

            {/* Logo Upload */}
            <div className="space-y-2">
              <Label htmlFor="logo" className="text-sm font-medium text-gray-900">
                Brand Logo <span className="text-gray-400 font-normal">(Optional)</span>
              </Label>
              <div className="flex items-center gap-4">
                <Input
                  id="logo"
                  type="file"
                  accept="image/*"
                  onChange={(e) => setLogoFile(e.target.files?.[0] || null)}
                  className="border-gray-300 focus:border-gray-900"
                />
                {logoFile && (
                  <span className="text-sm text-gray-600">{logoFile.name}</span>
                )}
              </div>
            </div>

            {/* Product Image Upload */}
            <div className="space-y-2">
              <Label htmlFor="product" className="text-sm font-medium text-gray-900">
                Product Image <span className="text-gray-400 font-normal">(Optional)</span>
              </Label>
              <div className="flex items-center gap-4">
                <Input
                  id="product"
                  type="file"
                  accept="image/*"
                  onChange={(e) => setProductFile(e.target.files?.[0] || null)}
                  className="border-gray-300 focus:border-gray-900"
                />
                {productFile && (
                  <span className="text-sm text-gray-600">{productFile.name}</span>
                )}
              </div>
            </div>

            {/* Submit Button */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Button
                type="submit"
                disabled={mutation.isPending || !prompt}
                className="w-full bg-gray-900 text-white hover:bg-gray-800 h-12 text-sm font-medium tracking-wide uppercase"
              >
                {mutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Generate Advertisement
                  </>
                )}
              </Button>
            </motion.div>

            {mutation.isError && (
              <p className="text-sm text-red-600 text-center">
                Error: {mutation.error instanceof Error ? mutation.error.message : 'Failed to generate ad'}
              </p>
            )}
          </form>
        </CardContent>
      </Card>
    </motion.div>
  );
}

