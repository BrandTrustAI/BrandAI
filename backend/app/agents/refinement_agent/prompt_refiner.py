"""
Prompt refiner for improving ad generation prompts based on critique feedback.
Analyzes critique feedback and generates improved prompts that address specific issues.
"""
from typing import Dict, List, Optional
import json

from app.agents.critique_agent.analyzers.vision_analyzer import vision_analyzer
from app.services.logger import app_logger


class PromptRefiner:
    """Refine prompts based on critique feedback."""
    
    def __init__(self):
        """Initialize prompt refiner."""
        self.logger = app_logger
        self.vision_analyzer = vision_analyzer
    
    def refine_prompt(
        self,
        original_prompt: str,
        critique_feedback: Dict,
        brand_kit: Optional[Dict] = None,
        media_type: str = "image"
    ) -> Dict:
        """
        Refine prompt based on critique feedback.
        
        Args:
            original_prompt: Original user prompt
            critique_feedback: Critique report with scores and feedback
            brand_kit: Brand kit information
            media_type: 'image' or 'video'
        
        Returns:
            Dictionary with refined prompt and improvement details
        """
        self.logger.info("Refining prompt based on critique feedback")
        
        try:
            # Extract issues and scores from critique feedback
            issues = self._extract_issues(critique_feedback)
            low_scores = self._identify_low_scores(critique_feedback)
            
            # Create refinement prompt for Gemini
            refinement_prompt = self._create_refinement_prompt(
                original_prompt,
                issues,
                low_scores,
                brand_kit,
                media_type
            )
            
            # Use Gemini to generate improved prompt
            # Note: We're using text generation, not vision, so we'll use Gemini API directly
            improved_prompt = self._generate_improved_prompt(refinement_prompt)
            
            # Extract improvement details
            improvements = self._extract_improvements(improved_prompt, issues)
            
            return {
                "success": True,
                "original_prompt": original_prompt,
                "refined_prompt": improved_prompt.get("prompt", original_prompt),
                "improvements": improvements,
                "addressed_issues": issues,
                "metadata": {
                    "low_scores": low_scores,
                    "improvement_reasoning": improved_prompt.get("reasoning", "")
                }
            }
        except Exception as e:
            self.logger.error(f"Error refining prompt: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_prompt": original_prompt,
                "refined_prompt": original_prompt  # Fallback to original
            }
    
    def _extract_issues(self, critique_feedback: Dict) -> List[str]:
        """Extract specific issues from critique feedback."""
        issues = []
        
        # Check variation results
        variations = critique_feedback.get("all_variations", [])
        if variations:
            # Get the first (or best) variation
            variation = variations[0] if variations else {}
            scorecard = variation.get("scorecard", [])
            
            for dimension in scorecard:
                dim_issues = dimension.get("issues", [])
                if dim_issues:
                    issues.extend(dim_issues)
                
                # Also check if score is low
                if dimension.get("score", 1.0) < 0.6:
                    dim_name = dimension.get("dimension", "")
                    issues.append(f"Low {dim_name} score: {dimension.get('feedback', '')}")
        
        return list(set(issues))  # Remove duplicates
    
    def _identify_low_scores(self, critique_feedback: Dict) -> Dict[str, float]:
        """Identify dimensions with low scores."""
        low_scores = {}
        
        variations = critique_feedback.get("all_variations", [])
        if variations:
            variation = variations[0] if variations else {}
            scorecard = variation.get("scorecard", [])
            
            for dimension in scorecard:
                dim_name = dimension.get("dimension", "")
                score = dimension.get("score", 1.0)
                if score < 0.7:  # Threshold for "low" score
                    low_scores[dim_name] = score
        
        return low_scores
    
    def _create_refinement_prompt(
        self,
        original_prompt: str,
        issues: List[str],
        low_scores: Dict[str, float],
        brand_kit: Optional[Dict],
        media_type: str
    ) -> str:
        """Create prompt for Gemini to refine the original prompt."""
        
        brand_context = ""
        if brand_kit:
            brand_name = brand_kit.get("brand_name", "")
            colors = brand_kit.get("colors", {})
            color_palette = colors.get("color_palette", [])
            
            if brand_name:
                brand_context += f"Brand: {brand_name}\n"
            if color_palette:
                brand_context += f"Brand colors: {', '.join(color_palette[:3])}\n"
        
        issues_text = "\n".join([f"- {issue}" for issue in issues]) if issues else "None identified"
        low_scores_text = "\n".join([f"- {dim}: {score:.2f}" for dim, score in low_scores.items()]) if low_scores else "None"
        
        prompt = f"""You are an expert prompt engineer for {media_type} advertisement generation.

ORIGINAL PROMPT:
{original_prompt}

{brand_context}
CRITIQUE FEEDBACK:
Issues found:
{issues_text}

Low scores:
{low_scores_text}

TASK:
Analyze the critique feedback and create an IMPROVED prompt that addresses the identified issues while maintaining the original intent.

The improved prompt should:
1. Address all identified issues
2. Maintain the original creative intent
3. Include specific improvements for low-scoring dimensions
4. Be clear and detailed for better {media_type} generation
5. Incorporate brand context if provided

Respond with JSON format:
{{
  "prompt": "improved prompt text here",
  "reasoning": "explanation of what was changed and why",
  "improvements": ["list of specific improvements made"]
}}

Be specific and actionable in your improvements."""
        
        return prompt
    
    def _generate_improved_prompt(self, refinement_prompt: str) -> Dict:
        """Use Gemini to generate improved prompt."""
        try:
            # Use Gemini API for text generation
            import google.generativeai as genai
            from app.config import settings
            
            # Initialize Gemini
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured")
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Try multiple model names
            model_names = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
            model = None
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    break
                except:
                    continue
            
            if not model:
                raise ValueError("Could not initialize any Gemini model")
            
            # Generate improved prompt
            response = model.generate_content(refinement_prompt)
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # Try to parse JSON response
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return parsed
            except Exception as parse_error:
                self.logger.warning(f"Could not parse JSON from response: {parse_error}")
            
            # Fallback: treat entire response as prompt
            return {
                "prompt": response_text.strip(),
                "reasoning": "Generated improved prompt based on critique feedback",
                "improvements": ["Prompt refined to address critique issues"]
            }
        except Exception as e:
            self.logger.error(f"Error generating improved prompt with Gemini: {e}")
            # Fallback: return basic improved prompt
            return {
                "prompt": refinement_prompt,  # Fallback to original
                "reasoning": f"Error during refinement: {str(e)}",
                "improvements": []
            }
    
    def _extract_improvements(self, improved_prompt: Dict, issues: List[str]) -> List[str]:
        """Extract list of improvements made."""
        improvements = improved_prompt.get("improvements", [])
        
        # If no improvements listed, create from issues addressed
        if not improvements and issues:
            improvements = [f"Addressed: {issue}" for issue in issues[:5]]  # Limit to 5
        
        return improvements


# Global prompt refiner instance
prompt_refiner = PromptRefiner()
