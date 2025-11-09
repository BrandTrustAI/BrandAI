"""
Message clarity evaluator.
Evaluates product visibility, text clarity, and message understanding.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.agents.critique_agent.evaluators.base_evaluator import BaseEvaluator
from app.agents.critique_agent.analyzers.clip_analyzer import clip_analyzer
from app.agents.critique_agent.analyzers.vision_analyzer import vision_analyzer
from app.services.logger import app_logger


class ClarityEvaluator(BaseEvaluator):
    """Evaluate message clarity of generated ads."""
    
    def __init__(self):
        """Initialize clarity evaluator."""
        super().__init__()
        self.clip_analyzer = clip_analyzer
        self.vision_analyzer = vision_analyzer
    
    def evaluate(
        self,
        ad_path: Path,
        brand_kit: Optional[Dict] = None,
        media_type: str = "image",
        **kwargs
    ) -> Dict:
        """
        Evaluate message clarity of ad.
        
        Args:
            ad_path: Path to generated ad
            brand_kit: Brand kit information
            media_type: 'image' or 'video'
            **kwargs: Additional parameters
        
        Returns:
            Evaluation result dictionary
        """
        self.logger.info(f"Evaluating message clarity for: {ad_path}")
        
        try:
            scores = []
            issues = []
            suggestions = []
            feedback_parts = []
            
            # 1. Product visibility
            user_prompt = kwargs.get("user_prompt")
            product_score, product_feedback, product_issues, product_suggestions = self._evaluate_product_visibility(
                ad_path, brand_kit, media_type, user_prompt=user_prompt
            )
            scores.append(product_score)
            if product_issues:
                issues.extend(product_issues)
            if product_suggestions:
                suggestions.extend(product_suggestions)
            feedback_parts.append(product_feedback)
            
            # 2. Text clarity (if applicable)
            user_prompt = kwargs.get("user_prompt")
            text_score, text_feedback, text_issues = self._evaluate_text_clarity(
                ad_path, media_type, user_prompt=user_prompt
            )
            scores.append(text_score)
            if text_issues:
                issues.extend(text_issues)
            feedback_parts.append(text_feedback)
            
            # 3. Message understanding
            message_score, message_feedback, message_issues = self._evaluate_message_understanding(
                ad_path, brand_kit, media_type, user_prompt=user_prompt
            )
            scores.append(message_score)
            if message_issues:
                issues.extend(message_issues)
            feedback_parts.append(message_feedback)
            
            # Calculate overall clarity score
            overall_score = sum(scores) / len(scores) if scores else 0.0
            
            # Combine feedback
            feedback = " | ".join(feedback_parts)
            
            return self.create_result(
                score=overall_score,
                feedback=feedback,
                issues=issues if issues else None,
                suggestions=suggestions if suggestions else None,
                metadata={
                    "product_score": product_score,
                    "text_score": text_score,
                    "message_score": message_score
                }
            )
        except Exception as e:
            self.logger.error(f"Error evaluating message clarity: {e}")
            return self.create_result(
                score=0.0,
                feedback=f"Error during clarity evaluation: {str(e)}",
                issues=[f"Evaluation error: {str(e)}"]
            )
    
    def _evaluate_product_visibility(
        self,
        ad_path: Path,
        brand_kit: Optional[Dict],
        media_type: str,
        user_prompt: Optional[str] = None
    ) -> Tuple[float, str, List[str], List[str]]:
        """Evaluate if product is visible and recognizable."""
        product_path = brand_kit.get("product", {}).get("file_path") if brand_kit else None
        
        # For videos, rely on Gemini Video API (handles product detection)
        if media_type == "video":
            # Gemini Video will handle product detection in comprehensive analysis
            return 0.7, "Product visibility handled by Gemini Video analysis", [], []
        
        # For images, use CLIP if product reference available, otherwise use Gemini
        if not product_path or not Path(product_path).exists():
            # No product reference, use Vision Analyzer to check if product-like objects are visible
            return self._evaluate_product_visibility_vision(ad_path, media_type, user_prompt=user_prompt)
        
        try:
            # Use CLIP to match product (more accurate for images)
            product_match = self.clip_analyzer.match_product(ad_path, Path(product_path))
            
            similarity = product_match.get("similarity_score", 0.0)
            product_detected = product_match.get("product_detected", False)
            
            if product_detected:
                score = min(1.0, similarity * 1.1)  # Boost if detected
                feedback = f"Product clearly visible (similarity: {similarity:.2f})"
                issues = []
                suggestions = []
            elif similarity >= 0.3:
                score = similarity * 0.8
                feedback = f"Product partially visible (similarity: {similarity:.2f})"
                issues = ["Product may not be prominent enough"]
                suggestions = ["Make product more central in composition"]
            else:
                score = similarity * 0.5
                feedback = f"Product not clearly visible (similarity: {similarity:.2f})"
                issues = ["Product not recognizable"]
                suggestions = ["Increase product visibility", "Make product larger/more prominent"]
            
            return score, feedback, issues, suggestions
        except Exception as e:
            self.logger.error(f"Error evaluating product visibility: {e}")
            return 0.5, "Product visibility evaluation error", [str(e)], []
    
    def _evaluate_product_visibility_vision(
        self,
        ad_path: Path,
        media_type: str,
        user_prompt: Optional[str] = None
    ) -> Tuple[float, str, List[str], List[str]]:
        """Evaluate product visibility using Vision Analyzer when no reference available."""
        try:
            prompt = "Is there a product clearly visible in this advertisement? Describe what product or item is shown."
            analysis = self.vision_analyzer.analyze_advertisement(ad_path, media_type, None, user_prompt=user_prompt)
            
            if not analysis.get("success"):
                return 0.5, "Product visibility check unavailable", ["Vision analysis failed"], []
            
            raw_text = analysis.get("raw_text", "").lower()
            
            # Heuristic: check for product-related keywords
            product_keywords = ["product", "item", "object", "visible", "shown", "displayed", "clear"]
            negative_keywords = ["no product", "not visible", "unclear", "hidden", "obscured"]
            
            positive_count = sum(1 for kw in product_keywords if kw in raw_text)
            negative_count = sum(1 for kw in negative_keywords if kw in raw_text)
            
            # Initialize suggestions
            suggestions = []
            
            if positive_count > negative_count and positive_count >= 2:
                score = 0.8
                feedback = "Product appears to be visible"
                issues = []
            elif positive_count > 0:
                score = 0.6
                feedback = "Product may be visible but not prominent"
                issues = ["Product visibility unclear"]
                suggestions = ["Make product more prominent"]
            else:
                score = 0.4
                feedback = "Product visibility unclear"
                issues = ["Product may not be clearly visible"]
                suggestions = ["Ensure product is clearly visible and prominent"]
            
            return score, feedback, issues, suggestions
        except Exception as e:
            self.logger.error(f"Error in vision-based product evaluation: {e}")
            return 0.5, "Product visibility evaluation error", [str(e)], []
    
    def _evaluate_text_clarity(
        self,
        ad_path: Path,
        media_type: str,
        user_prompt: Optional[str] = None
    ) -> Tuple[float, str, List[str]]:
        """Evaluate text clarity (if text is present)."""
        try:
            # Use Vision Analyzer to check for text
            prompt = "Is there any text, tagline, or words visible in this advertisement? If yes, is the text clear and readable?"
            analysis = self.vision_analyzer.analyze_advertisement(ad_path, media_type, None, user_prompt=user_prompt)
            
            if not analysis.get("success"):
                return 0.7, "Text clarity check unavailable", ["Vision analysis failed"]
            
            raw_text = analysis.get("raw_text", "").lower()
            
            # Heuristic: check for text-related keywords
            text_keywords = ["text", "readable", "clear", "visible", "tagline", "words"]
            clarity_keywords = ["clear", "readable", "legible", "visible"]
            negative_keywords = ["unclear", "blurry", "not readable", "illegible", "hard to read"]
            
            has_text = any(kw in raw_text for kw in text_keywords)
            is_clear = any(kw in raw_text for kw in clarity_keywords)
            is_unclear = any(kw in raw_text for kw in negative_keywords)
            
            if has_text and is_clear and not is_unclear:
                score = 1.0
                feedback = "Text is clear and readable"
                issues = []
            elif has_text and not is_unclear:
                score = 0.7
                feedback = "Text is present and mostly readable"
                issues = []
            elif has_text and is_unclear:
                score = 0.4
                feedback = "Text is present but not clearly readable"
                issues = ["Text clarity issues"]
            else:
                score = 0.8  # No text is fine for some ads
                feedback = "No text detected (may be acceptable)"
                issues = []
            
            return score, feedback, issues
        except Exception as e:
            self.logger.error(f"Error evaluating text clarity: {e}")
            return 0.7, "Text clarity evaluation error", [str(e)]
    
    def _evaluate_message_understanding(
        self,
        ad_path: Path,
        brand_kit: Optional[Dict],
        media_type: str,
        user_prompt: Optional[str] = None
    ) -> Tuple[float, str, List[str]]:
        """Evaluate if the message is clear and understandable."""
        try:
            # Use Vision Analyzer for comprehensive message analysis
            analysis = self.vision_analyzer.analyze_advertisement(ad_path, media_type, brand_kit, user_prompt=user_prompt)
            
            if not analysis.get("success"):
                return 0.5, "Message understanding check unavailable", ["Vision analysis failed"]
            
            raw_text = analysis.get("raw_text", "").lower()
            
            # Heuristic: check for message clarity indicators
            clarity_keywords = ["clear", "understandable", "obvious", "evident", "message", "convey"]
            confusion_keywords = ["unclear", "confusing", "ambiguous", "unclear message", "hard to understand"]
            
            clarity_count = sum(1 for kw in clarity_keywords if kw in raw_text)
            confusion_count = sum(1 for kw in confusion_keywords if kw in raw_text)
            
            if clarity_count > confusion_count and clarity_count >= 2:
                score = 0.9
                feedback = "Message is clear and understandable"
                issues = []
            elif clarity_count > 0:
                score = 0.7
                feedback = "Message is mostly clear"
                issues = []
            elif confusion_count > 0:
                score = 0.4
                feedback = "Message may be unclear or confusing"
                issues = ["Message clarity needs improvement"]
            else:
                score = 0.6
                feedback = "Message clarity assessment inconclusive"
                issues = []
            
            return score, feedback, issues
        except Exception as e:
            self.logger.error(f"Error evaluating message understanding: {e}")
            return 0.5, "Message understanding evaluation error", [str(e)]


# Global clarity evaluator instance
clarity_evaluator = ClarityEvaluator()
