"""
Refinement Agent - Improves ads based on critique feedback.
Decides between enhancement (OpenCV) vs regeneration (improved prompt).
"""
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

from app.agents.base_agent import BaseAgent
from app.agents.refinement_agent.prompt_refiner import prompt_refiner
from app.agents.refinement_agent.utils import image_enhancer
from app.services.logger import app_logger


class RefinementStrategy(Enum):
    """Refinement strategy options."""
    ENHANCE = "enhance"  # Use OpenCV to fix simple issues
    REGENERATE = "regenerate"  # Improve prompt and regenerate
    APPROVE = "approve"  # No refinement needed
    REJECT = "reject"  # Cannot be fixed


class RefinementAgent(BaseAgent):
    """Agent for refining ads based on critique feedback."""
    
    def __init__(self):
        """Initialize refinement agent."""
        super().__init__()
        self.logger = app_logger
        self.prompt_refiner = prompt_refiner
        self.image_enhancer = image_enhancer
    
    def execute(
        self,
        ad_path: str,
        critique_feedback: Dict,
        original_prompt: str,
        brand_kit: Optional[Dict] = None,
        media_type: str = "image",
        run_id: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        Execute refinement based on critique feedback.
        
        Args:
            ad_path: Path to generated ad that needs refinement
            critique_feedback: Critique report with scores and feedback
            original_prompt: Original prompt used for generation
            brand_kit: Brand kit information
            media_type: 'image' or 'video'
            run_id: Run ID for tracking
            **kwargs: Additional arguments
        
        Returns:
            Standardized result dictionary with refinement details
        """
        self.log_start("refinement", run_id=run_id, ad_path=ad_path)
        
        try:
            # Determine refinement strategy
            strategy = self._determine_strategy(critique_feedback, media_type)
            
            self.logger.info(f"Refinement strategy: {strategy.value}")
            
            if strategy == RefinementStrategy.APPROVE:
                return self._create_result(
                    success=True,
                    strategy="approve",
                    message="Ad meets quality standards, no refinement needed",
                    refined_ad_path=ad_path,
                    metadata={"original_score": self._get_overall_score(critique_feedback)}
                )
            
            elif strategy == RefinementStrategy.REJECT:
                return self._create_result(
                    success=False,
                    strategy="reject",
                    message="Ad has critical issues that cannot be fixed automatically",
                    refined_ad_path=ad_path,
                    metadata={"issues": self._get_critical_issues(critique_feedback)}
                )
            
            elif strategy == RefinementStrategy.ENHANCE:
                # Use OpenCV to enhance image
                return self._enhance_ad(ad_path, critique_feedback, media_type, run_id)
            
            elif strategy == RefinementStrategy.REGENERATE:
                # Improve prompt and return refined prompt for regeneration
                return self._refine_prompt_for_regeneration(
                    original_prompt, critique_feedback, brand_kit, media_type
                )
            
            else:
                return self._create_result(
                    success=False,
                    strategy="unknown",
                    message=f"Unknown strategy: {strategy}",
                    refined_ad_path=ad_path
                )
        
        except Exception as e:
            self.logger.error(f"Error in refinement agent: {e}")
            return self._create_result(
                success=False,
                strategy="error",
                message=f"Refinement error: {str(e)}",
                refined_ad_path=ad_path
            )
    
    def _determine_strategy(
        self,
        critique_feedback: Dict,
        media_type: str
    ) -> RefinementStrategy:
        """
        Determine refinement strategy based on critique feedback.
        
        Decision logic:
        - APPROVE: Overall score >= 0.7 and no critical issues
        - ENHANCE: Overall score < 0.7 but only simple issues (blur, noise, contrast)
        - REGENERATE: Complex issues (brand alignment, message clarity, safety)
        - REJECT: Critical safety issues or overall score < 0.3
        """
        overall_score = self._get_overall_score(critique_feedback)
        
        # Check for critical safety issues
        if self._has_critical_safety_issues(critique_feedback):
            return RefinementStrategy.REJECT
        
        # If score is very low, reject
        if overall_score < 0.3:
            return RefinementStrategy.REJECT
        
        # If score is good enough, approve
        if overall_score >= 0.7:
            return RefinementStrategy.APPROVE
        
        # Check if issues are simple (can be fixed with OpenCV)
        if media_type == "image" and self._has_only_simple_issues(critique_feedback):
            return RefinementStrategy.ENHANCE
        
        # Otherwise, regenerate with improved prompt
        return RefinementStrategy.REGENERATE
    
    def _get_overall_score(self, critique_feedback: Dict) -> float:
        """Get overall score from critique feedback."""
        variations = critique_feedback.get("all_variations", [])
        if variations:
            return variations[0].get("overall_score", 0.0)
        return 0.0
    
    def _has_critical_safety_issues(self, critique_feedback: Dict) -> bool:
        """Check if there are critical safety issues."""
        variations = critique_feedback.get("all_variations", [])
        if not variations:
            return False
        
        variation = variations[0]
        scorecard = variation.get("scorecard", [])
        
        for dimension in scorecard:
            if dimension.get("dimension") == "safety_ethics":
                score = dimension.get("score", 1.0)
                if score < 0.3:  # Critical safety issue
                    return True
        
        return False
    
    def _has_only_simple_issues(self, critique_feedback: Dict) -> bool:
        """
        Check if issues are simple (can be fixed with OpenCV).
        Simple issues: blur, noise, contrast, brightness
        Complex issues: brand alignment, message clarity, safety
        """
        variations = critique_feedback.get("all_variations", [])
        if not variations:
            return False
        
        variation = variations[0]
        scorecard = variation.get("scorecard", [])
        
        simple_issue_keywords = ["blur", "noise", "artifact", "contrast", "brightness", "sharp"]
        complex_issue_keywords = ["brand", "logo", "color", "message", "product", "safety", "stereotype"]
        
        for dimension in scorecard:
            dim_name = dimension.get("dimension", "").lower()
            feedback = dimension.get("feedback", "").lower()
            issues = dimension.get("issues", [])
            
            # Check dimension name
            if any(kw in dim_name for kw in complex_issue_keywords):
                if dimension.get("score", 1.0) < 0.7:
                    return False  # Complex issue found
            
            # Check feedback and issues
            all_text = feedback + " " + " ".join(issues)
            if any(kw in all_text for kw in complex_issue_keywords):
                if dimension.get("score", 1.0) < 0.7:
                    return False  # Complex issue found
        
        # Only simple issues found
        return True
    
    def _get_critical_issues(self, critique_feedback: Dict) -> List[str]:
        """Get list of critical issues."""
        issues = []
        variations = critique_feedback.get("all_variations", [])
        
        if variations:
            variation = variations[0]
            scorecard = variation.get("scorecard", [])
            
            for dimension in scorecard:
                if dimension.get("score", 1.0) < 0.5:
                    dim_name = dimension.get("dimension", "")
                    dim_issues = dimension.get("issues", [])
                    issues.append(f"{dim_name}: {', '.join(dim_issues) if dim_issues else 'Low score'}")
        
        return issues
    
    def _enhance_ad(
        self,
        ad_path: str,
        critique_feedback: Dict,
        media_type: str,
        run_id: Optional[str]
    ) -> Dict:
        """Enhance ad using OpenCV."""
        if media_type != "image":
            return self._create_result(
                success=False,
                strategy="enhance",
                message="Enhancement only supported for images, not videos",
                refined_ad_path=ad_path
            )
        
        try:
            # Determine which enhancements to apply
            enhancements = self._determine_enhancements(critique_feedback)
            
            if not any(enhancements.values()):
                return self._create_result(
                    success=False,
                    strategy="enhance",
                    message="No applicable enhancements identified",
                    refined_ad_path=ad_path
                )
            
            # Create output path
            ad_path_obj = Path(ad_path)
            output_path = ad_path_obj.parent / f"{ad_path_obj.stem}_enhanced{ad_path_obj.suffix}"
            
            # Apply enhancements
            result = self.image_enhancer.enhance_image(
                ad_path_obj,
                output_path,
                enhancements
            )
            
            if result.get("success"):
                self.log_complete("refinement", run_id=run_id)
                return self._create_result(
                    success=True,
                    strategy="enhance",
                    message=f"Image enhanced: {', '.join(result.get('enhancements_applied', []))}",
                    refined_ad_path=str(output_path),
                    metadata=result
                )
            else:
                return self._create_result(
                    success=False,
                    strategy="enhance",
                    message=f"Enhancement failed: {result.get('error', 'Unknown error')}",
                    refined_ad_path=ad_path
                )
        
        except Exception as e:
            self.logger.error(f"Error enhancing ad: {e}")
            return self._create_result(
                success=False,
                strategy="enhance",
                message=f"Enhancement error: {str(e)}",
                refined_ad_path=ad_path
            )
    
    def _determine_enhancements(self, critique_feedback: Dict) -> Dict[str, bool]:
        """Determine which enhancements to apply based on critique feedback."""
        enhancements = {
            "sharpen": False,
            "denoise": False,
            "contrast": False,
            "brightness": False
        }
        
        variations = critique_feedback.get("all_variations", [])
        if not variations:
            return enhancements
        
        variation = variations[0]
        scorecard = variation.get("scorecard", [])
        
        for dimension in scorecard:
            feedback = dimension.get("feedback", "").lower()
            issues = dimension.get("issues", [])
            all_text = feedback + " " + " ".join(issues).lower()
            
            # Check for blur/sharpness issues
            if any(kw in all_text for kw in ["blur", "blurry", "unsharp", "soft"]):
                enhancements["sharpen"] = True
            
            # Check for noise issues
            if any(kw in all_text for kw in ["noise", "noisy", "artifact", "grain"]):
                enhancements["denoise"] = True
            
            # Check for contrast issues
            if any(kw in all_text for kw in ["contrast", "flat", "dull"]):
                enhancements["contrast"] = True
            
            # Check for brightness issues
            if any(kw in all_text for kw in ["bright", "dark", "brightness", "exposure"]):
                enhancements["brightness"] = True
        
        return enhancements
    
    def _refine_prompt_for_regeneration(
        self,
        original_prompt: str,
        critique_feedback: Dict,
        brand_kit: Optional[Dict],
        media_type: str
    ) -> Dict:
        """Refine prompt for regeneration."""
        try:
            result = self.prompt_refiner.refine_prompt(
                original_prompt,
                critique_feedback,
                brand_kit,
                media_type
            )
            
            if result.get("success"):
                return self._create_result(
                    success=True,
                    strategy="regenerate",
                    message="Prompt refined for regeneration",
                    refined_prompt=result.get("refined_prompt", original_prompt),
                    metadata={
                        "improvements": result.get("improvements", []),
                        "addressed_issues": result.get("addressed_issues", [])
                    }
                )
            else:
                return self._create_result(
                    success=False,
                    strategy="regenerate",
                    message=f"Prompt refinement failed: {result.get('error', 'Unknown error')}",
                    refined_prompt=original_prompt
                )
        
        except Exception as e:
            self.logger.error(f"Error refining prompt: {e}")
            return self._create_result(
                success=False,
                strategy="regenerate",
                message=f"Prompt refinement error: {str(e)}",
                refined_prompt=original_prompt
            )
    
    def _create_result(
        self,
        success: bool,
        strategy: str,
        message: str,
        refined_ad_path: Optional[str] = None,
        refined_prompt: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Create standardized result dictionary."""
        result = {
            "success": success,
            "strategy": strategy,
            "message": message
        }
        
        if refined_ad_path:
            result["refined_ad_path"] = refined_ad_path
        
        if refined_prompt:
            result["refined_prompt"] = refined_prompt
        
        if metadata:
            result["metadata"] = metadata
        
        return result


# Global refinement agent instance
refinement_agent = RefinementAgent()
