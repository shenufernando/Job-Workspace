import pytest
import os
import sys

# Append backend directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ai_matching import load_ai_models, get_ranked_workers
import utils.ai_matching as ai

def test_artifacts_load():
    """Verify that the BERT model and tokenizers load successfully from the saved directory."""
    # This might take a few seconds during the test suite execution.
    success = load_ai_models()
    
    assert success is True
    assert ai.model is not None
    assert ai.tokenizer is not None
    assert ai.label_encoder is not None

def test_embedding_shape():
    """Verify the tokenization output generates the exact tensor shape required by BERT."""
    if ai.model is None or ai.tokenizer is None:
        load_ai_models()
        
    sample_text = "Looking for a specialized auto mechanic with 5 years experience."
    
    inputs = ai.tokenizer(sample_text, return_tensors="pt", truncation=True, padding=True, max_length=128).to(ai.device)
    
    assert 'input_ids' in inputs
    assert 'attention_mask' in inputs
    assert inputs['input_ids'].shape[0] == 1  # Batch size 1
    assert inputs['input_ids'].shape[1] > 0   # Contains tokens

def test_semantic_matching_score():
    """Verify the cosine similarity logic ranks matching skills higher than unrelated string inputs."""
    
    if ai.model is None or ai.tokenizer is None:
        load_ai_models()
        
    # Mocking Job Post
    job = {
        "title": "Senior Plumber",
        "required_skills": "pipe fitting, water heater installation, leak repair"
    }
    
    # Mocking two distinct workers
    worker_good = {
        "id": 1,
        "position": "Plumber",
        "skills": "fixing pipes, repairing water heaters, plumbing"
    }
    
    worker_bad = {
        "id": 2,
        "position": "Electrician",
        "skills": "wiring, circuit boards, high voltage"
    }
    
    workers = [worker_good, worker_bad]
    
    ranked_workers = get_ranked_workers(job, workers)
    
    # 1. The bad worker should be filtered out because their skills are completely unrelated (score < 50)
    assert len(ranked_workers) == 1
    
    # 2. Extract final match percentage of the good worker
    good_worker = ranked_workers[0]
    assert good_worker['id'] == 1
    
    good_score = good_worker.get('final_match_percentage', 0)
    
    # Base score verification
    assert good_score > 50 
