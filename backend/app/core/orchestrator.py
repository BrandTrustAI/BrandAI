"""
LangGraph workflow orchestrator for BrandAI.
Orchestrates the complete ad generation workflow:
Brand Kit → Generation → Critique → Refinement (if needed)
"""
from typing import TypedDict, List, Optional, Dict, Literal, Annotated
from pathlib import Path
import operator

from langgraph.graph import StateGraph, END

from app.agents.brand_kit_agent.agent import BrandKitAgent
from app.agents.generation_agent.agent import GenerationAgent
from app.agents.critique_agent.agent import CritiqueAgent
from app.agents.refinement_agent.agent import RefinementAgent, RefinementStrategy
from app.core.run_manager import run_manager
from app.models.run import RunStatus
from app.services.storage_service import storage_service
from app.services.logger import app_logger
import json


# ============================================================================
# Workflow State Definition
# ============================================================================

class WorkflowState(TypedDict):
    """State for the LangGraph workflow."""
    
    # Input
    run_id: str
    user_prompt: str
    media_type: Literal["image", "video"]
    brand_website_url: Optional[str]
    logo_path: Optional[str]
    product_path: Optional[str]
    
    # Brand Kit
    brand_kit: Optional[Dict]
    brand_kit_extracted: bool
    
    # Generation
    generated_ad_path: Optional[str]
    generation_success: bool
    generation_error: Optional[str]
    
    # Critique
    critique_feedback: Optional[Dict]
    critique_success: bool
    critique_error: Optional[str]
    overall_score: Optional[float]
    
    # Refinement
    refinement_strategy: Optional[str]  # "approve", "regenerate", "enhance", "reject"
    refined_ad_path: Optional[str]
    refined_prompt: Optional[str]
    refinement_success: bool
    refinement_error: Optional[str]
    
    # Retry tracking
    retry_count: int
    max_retries: int
    
    # Final status
    workflow_status: Literal["in_progress", "completed", "failed", "rejected"]
    final_result: Optional[Dict]
    error_message: Optional[str]


# ============================================================================
# Agent Node Functions
# ============================================================================

def brand_kit_node(state: WorkflowState) -> WorkflowState:
    """Extract brand kit information."""
    logger = app_logger
    logger.info(f"[Workflow] Brand Kit Node - Run ID: {state['run_id']}")
    
    try:
        run_manager.start_stage(state['run_id'], "brand_kit_extraction")
        
        brand_kit_agent = BrandKitAgent()
        
        # Execute brand kit extraction
        logo_path = state.get("logo_path")
        product_path = state.get("product_path")
        
        # Convert string paths to Path objects if they exist
        logo_path_obj = Path(logo_path) if logo_path else None
        product_path_obj = Path(product_path) if product_path else None
        
        logger.info(f"Brand kit extraction - logo_path: {logo_path}, product_path: {product_path}")
        if logo_path_obj:
            logger.info(f"Logo path exists: {logo_path_obj.exists()}")
        if product_path_obj:
            logger.info(f"Product path exists: {product_path_obj.exists()}")
        
        result = brand_kit_agent.execute(
            brand_logo_path=logo_path_obj,
            product_image_path=product_path_obj,
            brand_website_url=state.get("brand_website_url"),
            run_id=state['run_id']
        )
        
        if result.get("success"):
            brand_kit = result.get("data", {}).get("brand_kit", {})
            run_manager.complete_stage(state['run_id'], "brand_kit_extraction")
            run_manager.update_status(state['run_id'], RunStatus.PROCESSING, progress=25.0, current_stage="brand_kit_extraction")
            
            return {
                **state,
                "brand_kit": brand_kit,
                "brand_kit_extracted": True
            }
        else:
            error = result.get("error", "Brand kit extraction failed")
            run_manager.fail_stage(state['run_id'], "brand_kit_extraction", error)
            
            return {
                **state,
                "brand_kit_extracted": False,
                "workflow_status": "failed",
                "error_message": error
            }
    
    except Exception as e:
        logger.error(f"Error in brand kit node: {e}")
        run_manager.fail_stage(state['run_id'], "brand_kit_extraction", str(e))
        
        return {
            **state,
            "brand_kit_extracted": False,
            "workflow_status": "failed",
            "error_message": str(e)
        }


def generation_node(state: WorkflowState) -> WorkflowState:
    """Generate advertisement."""
    logger = app_logger
    logger.info(f"[Workflow] Generation Node - Run ID: {state['run_id']}")
    
    try:
        run_manager.start_stage(state['run_id'], "ad_generation")
        
        # Use refined prompt if available, otherwise use original
        prompt = state.get("refined_prompt") or state['user_prompt']
        
        generation_agent = GenerationAgent()
        
        result = generation_agent.execute(
            prompt=prompt,
            media_type=state['media_type'],
            brand_kit=state.get("brand_kit"),
            run_id=state['run_id'],
            num_variations=1
        )
        
        if result.get("success"):
            data = result.get("data", {})
            variations = data.get("variations", [])
            
            if variations:
                generated_ad_path = variations[0].get("file_path")
                run_manager.complete_stage(state['run_id'], "ad_generation")
                run_manager.update_status(state['run_id'], RunStatus.PROCESSING, progress=50.0, current_stage="ad_generation")
                
                return {
                    **state,
                    "generated_ad_path": generated_ad_path,
                    "generation_success": True,
                    "refined_prompt": None  # Reset after use
                }
            else:
                error = "No variations generated"
                run_manager.fail_stage(state['run_id'], "ad_generation", error)
                
                return {
                    **state,
                    "generation_success": False,
                    "generation_error": error,
                    "workflow_status": "failed",
                    "error_message": error
                }
        else:
            error = result.get("error", "Generation failed")
            run_manager.fail_stage(state['run_id'], "ad_generation", error)
            
            return {
                **state,
                "generation_success": False,
                "generation_error": error,
                "workflow_status": "failed",
                "error_message": error
            }
    
    except Exception as e:
        logger.error(f"Error in generation node: {e}")
        run_manager.fail_stage(state['run_id'], "ad_generation", str(e))
        
        return {
            **state,
            "generation_success": False,
            "generation_error": str(e),
            "workflow_status": "failed",
            "error_message": str(e)
        }


def critique_node(state: WorkflowState) -> WorkflowState:
    """Critique generated advertisement."""
    logger = app_logger
    logger.info(f"[Workflow] Critique Node - Run ID: {state['run_id']}")
    
    try:
        run_manager.start_stage(state['run_id'], "critique")
        
        if not state.get("generated_ad_path"):
            error = "No generated ad to critique"
            return {
                **state,
                "critique_success": False,
                "critique_error": error,
                "workflow_status": "failed",
                "error_message": error
            }
        
        critique_agent = CritiqueAgent()
        
        result = critique_agent.execute(
            ad_paths=[state["generated_ad_path"]],
            brand_kit=state.get("brand_kit"),
            media_type=state['media_type'],
            run_id=state['run_id'],
            user_prompt=state['user_prompt']
        )
        
        if result.get("success"):
            data = result.get("data", {})
            critique_report = data.get("critique_report")
            
            # Convert to dict if Pydantic model
            if hasattr(critique_report, 'model_dump'):
                critique_feedback = critique_report.model_dump()
            elif hasattr(critique_report, 'dict'):
                critique_feedback = critique_report.dict()
            else:
                critique_feedback = critique_report
            
            # Extract overall score
            overall_score = 0.0
            if critique_feedback.get("all_variations"):
                overall_score = critique_feedback["all_variations"][0].get("overall_score", 0.0)
            
            run_manager.complete_stage(state['run_id'], "critique")
            run_manager.update_status(state['run_id'], RunStatus.PROCESSING, progress=75.0, current_stage="critique")
            
            return {
                **state,
                "critique_feedback": critique_feedback,
                "critique_success": True,
                "overall_score": overall_score
            }
        else:
            error = result.get("error", "Critique failed")
            run_manager.fail_stage(state['run_id'], "critique", error)
            
            return {
                **state,
                "critique_success": False,
                "critique_error": error,
                "workflow_status": "failed",
                "error_message": error
            }
    
    except Exception as e:
        logger.error(f"Error in critique node: {e}")
        run_manager.fail_stage(state['run_id'], "critique", str(e))
        
        return {
            **state,
            "critique_success": False,
            "critique_error": str(e),
            "workflow_status": "failed",
            "error_message": str(e)
        }


def refinement_node(state: WorkflowState) -> WorkflowState:
    """Refine advertisement based on critique feedback."""
    logger = app_logger
    logger.info(f"[Workflow] Refinement Node - Run ID: {state['run_id']}")
    
    try:
        run_manager.start_stage(state['run_id'], "refinement")
        
        if not state.get("critique_feedback") or not state.get("generated_ad_path"):
            error = "Missing critique feedback or generated ad"
            return {
                **state,
                "refinement_success": False,
                "refinement_error": error,
                "workflow_status": "failed",
                "error_message": error
            }
        
        refinement_agent = RefinementAgent()
        
        result = refinement_agent.execute(
            ad_path=state["generated_ad_path"],
            critique_feedback=state["critique_feedback"],
            original_prompt=state['user_prompt'],
            brand_kit=state.get("brand_kit"),
            media_type=state['media_type'],
            run_id=state['run_id']
        )
        
        strategy = result.get("strategy", "unknown")
        success = result.get("success", False)
        
        run_manager.complete_stage(state['run_id'], "refinement")
        run_manager.update_status(state['run_id'], RunStatus.PROCESSING, progress=90.0, current_stage="refinement")
        
        return {
            **state,
            "refinement_strategy": strategy,
            "refined_ad_path": result.get("refined_ad_path"),
            "refined_prompt": result.get("refined_prompt"),
            "refinement_success": success,
            "refinement_error": result.get("message") if not success else None
        }
    
    except Exception as e:
        logger.error(f"Error in refinement node: {e}")
        run_manager.fail_stage(state['run_id'], "refinement", str(e))
        
        return {
            **state,
            "refinement_success": False,
            "refinement_error": str(e),
            "workflow_status": "failed",
            "error_message": str(e)
        }


# ============================================================================
# Decision Logic
# ============================================================================

def should_continue(state: WorkflowState) -> Literal["approve", "regenerate", "enhance", "reject", "end"]:
    """
    Decide next step based on refinement strategy.
    
    Returns:
        "approve": Ad is good, workflow complete
        "regenerate": Need to regenerate with improved prompt
        "enhance": Need to enhance and re-critique
        "reject": Cannot be fixed, workflow failed
        "end": Error or max retries reached
    """
    strategy = state.get("refinement_strategy")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    if not strategy:
        return "end"
    
    if strategy == "approve":
        return "approve"
    
    elif strategy == "reject":
        return "reject"
    
    elif strategy == "regenerate":
        if retry_count >= max_retries:
            return "end"  # Max retries reached
        return "regenerate"
    
    elif strategy == "enhance":
        # After enhancement, go back to critique
        return "enhance"
    
    else:
        return "end"


# ============================================================================
# Workflow Graph Construction
# ============================================================================

def create_workflow_graph() -> StateGraph:
    """Create and compile the LangGraph workflow."""
    
    # Create state graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("brand_kit", brand_kit_node)
    workflow.add_node("generation", generation_node)
    workflow.add_node("critique", critique_node)
    workflow.add_node("refinement", refinement_node)
    
    # Define edges
    workflow.set_entry_point("brand_kit")
    
    # Sequential flow
    workflow.add_edge("brand_kit", "generation")
    workflow.add_edge("generation", "critique")
    workflow.add_edge("critique", "refinement")
    
    # Conditional routing from refinement
    workflow.add_conditional_edges(
        "refinement",
        should_continue,
        {
            "approve": END,
            "reject": END,
            "regenerate": "generation",  # Loop back to generation
            "enhance": "critique",  # Loop back to critique (after enhancement)
            "end": END
        }
    )
    
    # Compile workflow
    app = workflow.compile()
    
    return app


# ============================================================================
# Orchestrator Class
# ============================================================================

class WorkflowOrchestrator:
    """Orchestrates the complete ad generation workflow."""
    
    def __init__(self):
        """Initialize orchestrator."""
        self.logger = app_logger
        self.workflow = create_workflow_graph()
    
    def execute(
        self,
        run_id: str,
        user_prompt: str,
        media_type: Literal["image", "video"],
        brand_website_url: Optional[str] = None,
        logo_path: Optional[str] = None,
        product_path: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict:
        """
        Execute the complete workflow.
        
        Args:
            run_id: Unique run ID
            user_prompt: User-provided prompt
            media_type: 'image' or 'video'
            brand_website_url: Optional brand website URL
            logo_path: Optional logo file path
            product_path: Optional product image path
            max_retries: Maximum retry attempts (default: 3)
        
        Returns:
            Dictionary with workflow results
        """
        self.logger.info(f"Starting workflow execution - Run ID: {run_id}")
        
        # Create initial state
        initial_state: WorkflowState = {
            "run_id": run_id,
            "user_prompt": user_prompt,
            "media_type": media_type,
            "brand_website_url": brand_website_url,
            "logo_path": logo_path,
            "product_path": product_path,
            "brand_kit": None,
            "brand_kit_extracted": False,
            "generated_ad_path": None,
            "generation_success": False,
            "generation_error": None,
            "critique_feedback": None,
            "critique_success": False,
            "critique_error": None,
            "overall_score": None,
            "refinement_strategy": None,
            "refined_ad_path": None,
            "refined_prompt": None,
            "refinement_success": False,
            "refinement_error": None,
            "retry_count": 0,
            "max_retries": max_retries,
            "workflow_status": "in_progress",
            "final_result": None,
            "error_message": None
        }
        
        # Initialize progress
        run_manager.update_status(run_id, RunStatus.PROCESSING, progress=0.0, current_stage="initializing")
        
        try:
            # Execute workflow
            self.logger.info(f"[Orchestrator] Starting workflow stream - Run ID: {run_id}")
            final_state = None
            node_count = 0
            
            for output in self.workflow.stream(initial_state):
                node_count += 1
                self.logger.info(f"[Orchestrator] Workflow step {node_count} - Run ID: {run_id}")
                
                # LangGraph 1.0 returns dict with node names as keys
                if isinstance(output, dict):
                    # Get the last node's output
                    node_name = list(output.keys())[-1] if output else None
                    if node_name:
                        node_state = output[node_name]
                        final_state = node_state
                        self.logger.info(f"[Orchestrator] Node '{node_name}' completed - Run ID: {run_id}")
                        
                        # Update retry count if regenerating
                        if node_name == "refinement" and node_state.get("refinement_strategy") == "regenerate":
                            node_state["retry_count"] = node_state.get("retry_count", 0) + 1
                            self.logger.info(f"[Orchestrator] Regeneration triggered, retry count: {node_state['retry_count']}")
                else:
                    final_state = output
                    self.logger.info(f"[Orchestrator] Workflow step output received - Run ID: {run_id}")
            
            self.logger.info(f"[Orchestrator] Workflow stream completed after {node_count} steps - Run ID: {run_id}")
            
            # Get final state
            if not final_state:
                final_state = initial_state
                final_state["workflow_status"] = "failed"
                final_state["error_message"] = "Workflow execution failed"
            
            # Determine final status
            strategy = final_state.get("refinement_strategy")
            if strategy == "approve":
                final_state["workflow_status"] = "completed"
            elif strategy == "reject":
                final_state["workflow_status"] = "rejected"
            elif final_state.get("retry_count", 0) >= max_retries:
                final_state["workflow_status"] = "failed"
                final_state["error_message"] = "Maximum retries reached"
            
            # Create final result
            final_result = {
                "run_id": run_id,
                "status": final_state["workflow_status"],
                "success": final_state["workflow_status"] == "completed",
                "generated_ad_path": final_state.get("refined_ad_path") or final_state.get("generated_ad_path"),
                "critique_report": final_state.get("critique_feedback"),
                "overall_score": final_state.get("overall_score"),
                "retry_count": final_state.get("retry_count", 0),
                "error": final_state.get("error_message")
            }
            
            final_state["final_result"] = final_result
            
            # Update run manager with final results
            final_ad_path = final_result.get("generated_ad_path")
            critique_report = final_result.get("critique_report")
            
            # Save critique report to disk if available
            if critique_report:
                try:
                    # Convert to JSON string
                    if isinstance(critique_report, dict):
                        report_json = json.dumps(critique_report, indent=2, default=str)
                    else:
                        # If it's a Pydantic model, convert to dict first
                        if hasattr(critique_report, 'model_dump'):
                            report_dict = critique_report.model_dump()
                        elif hasattr(critique_report, 'dict'):
                            report_dict = critique_report.dict()
                        else:
                            report_dict = critique_report
                        report_json = json.dumps(report_dict, indent=2, default=str)
                    
                    # Save to disk
                    report_path = storage_service.save_report(
                        report_content=report_json,
                        run_id=run_id,
                        report_type="critique"
                    )
                    self.logger.info(f"Critique report saved to: {report_path}")
                except Exception as e:
                    self.logger.error(f"Error saving critique report to disk: {e}")
            
            # Store in run manager (in-memory)
            run_manager.update_run_data(
                run_id=run_id,
                final_ad_path=final_ad_path,
                critique_results=critique_report if critique_report else None
            )
            
            # Mark run as completed or failed
            if final_state["workflow_status"] == "completed":
                run_manager.update_status(run_id, RunStatus.PROCESSING, progress=100.0, current_stage="completed")
                run_manager.complete_run(run_id, success=True)
            else:
                run_manager.fail_run(run_id, final_state.get("error_message", "Workflow failed"))
            
            self.logger.info(f"Workflow completed - Run ID: {run_id}, Status: {final_state['workflow_status']}")
            
            return final_result
        
        except Exception as e:
            self.logger.error(f"Error executing workflow: {e}")
            run_manager.fail_run(run_id, str(e))
            
            return {
                "run_id": run_id,
                "status": "failed",
                "success": False,
                "error": str(e)
            }


# Global orchestrator instance
orchestrator = WorkflowOrchestrator()
