import os
import torch
import pickle
import numpy as np
from math import radians, cos, sin, asin, sqrt
from transformers import BertTokenizer, BertForSequenceClassification
import torch.nn.functional as F

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'bert_job_model')
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, 'bert_label_encoder.pkl')

# Global Variables
model = None
tokenizer = None
label_encoder = None
device = torch.device("cpu")

# --- SRI LANKA CITIES COORDINATES DATABASE ---
# අපි නිතර පාවිච්චි වන නගර වල Lat/Lon මෙතනම දාමු (API ඕනේ නෑ)
CITY_COORDS = {
    "colombo": (6.9271, 79.8612),
    "gampaha": (7.0840, 79.9939),
    "kandy": (7.2906, 80.6337),
    "galle": (6.0535, 80.2210),
    "matara": (5.9549, 80.5550),
    "kurunegala": (7.4863, 80.3647),
    "negombo": (7.2088, 79.8358),
    "jaffna": (9.6615, 80.0255),
    "anuradhapura": (8.3114, 80.4037),
    "trincomalee": (8.5874, 81.2152),
    "batticaloa": (7.7310, 81.6747),
    "kalutara": (6.5854, 79.9607),
    "panadura": (6.7106, 79.9074),
    "nuwara eliya": (6.9497, 80.7891),
    "badulla": (6.9934, 81.0550),
    "ratnapura": (6.6939, 80.3983),
    "kegalle": (7.2513, 80.3464),
    "matale": (7.4727, 80.6218),
    "hambantota": (6.1429, 81.1212),
    "kottawa": (6.8412, 79.9654),
    "maharagama": (6.8480, 79.9265),
    "nugegoda": (6.8649, 79.8997),
    "malabe": (6.9061, 79.9647),
    "homagama": (6.8445, 80.0007),
    "piliyandala": (6.8018, 79.9227),
    "moratuwa": (6.7730, 79.8816),
    "dehiwala": (6.8511, 79.8659),
    "kelaniya": (6.9543, 79.9173),
    "kadawatha": (7.0019, 79.9523)
}

def load_ai_models():
    global model, tokenizer, label_encoder
    print("⏳ Loading AI Models (BERT)...")
    try:
        with open(LABEL_ENCODER_PATH, 'rb') as f:
            label_encoder = pickle.load(f)
        tokenizer = BertTokenizer.from_pretrained(MODEL_DIR)
        model = BertForSequenceClassification.from_pretrained(MODEL_DIR)
        model.to(device)
        model.eval()
        print("✅ BERT Model Loaded Successfully!")
        return True
    except Exception as e:
        print(f"❌ Error loading AI: {e}")
        return False

# Function to calculate distance between two points (Haversine Formula)
def calculate_distance_km(city1, city2):
    c1 = CITY_COORDS.get(city1.lower().strip())
    c2 = CITY_COORDS.get(city2.lower().strip())
    
    if not c1 or not c2:
        return 999 # දුර හොයාගන්න බැරි නම් ලොකු අගයක් දෙනවා

    lon1, lat1, lon2, lat2 = map(radians, [c1[1], c1[0], c2[1], c2[0]])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return round(c * r, 1)

load_ai_models()

def get_ranked_workers(job_post, workers_list):
    matched_workers = []
    
    for worker in workers_list:
        # 1. Base Score Initialization (Give everyone a default baseline score of 50)
        base_score = 50
        
        # Safe String Extractions mapping Job Title against Worker Position
        w_pos = (worker.get('position') or '').lower().strip()
        j_tit = (job_post.get('title') or '').lower().strip()
        
        # Fuzzy Substring Base Scoring (Case-insensitive matching words)
        if w_pos and j_tit:
            if w_pos in j_tit or j_tit in w_pos:
                base_score = 100
            else:
                base_score = 30 # Unrelated positions drop to bottom
        else:
            base_score = 30
        
        # 2. Safe Skills Extraction for BERT
        raw_req_skills = job_post.get('required_skills') or ''
        job_skills = str(raw_req_skills).strip()
        has_req_skills = bool(job_skills)
        
        raw_w_skills = worker.get('skills') or ''
        worker_skills = str(raw_w_skills).strip()
        has_w_skills = bool(worker_skills)
        
        skill_score = 0
        final_score = base_score
        
        # 3. BERT Skills Blending Logic inside a Safe Wrapper
        if has_req_skills:
            if has_w_skills:
                try:
                    inputs1 = tokenizer(job_skills, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)
                    inputs2 = tokenizer(worker_skills, return_tensors="pt", truncation=True, padding=True, max_length=128).to(device)
                    
                    with torch.no_grad():
                        emb1 = model.bert(**inputs1).last_hidden_state.mean(dim=1)
                        emb2 = model.bert(**inputs2).last_hidden_state.mean(dim=1)
                    
                    cos_sim = F.cosine_similarity(emb1, emb2)[0].item()
                    skill_score = max(0, cos_sim * 100)
                    
                    # Blend the scores explicitly using int() bounding (50% Position, 50% Skills)
                    final_score = int((base_score * 0.5) + (skill_score * 0.5))
                except Exception as e:
                    print(f"Skills BERT Error: {e}", flush=True)
                    final_score = base_score
            else:
                # Worker has no skills but job requires them, penalize severely (50% block)
                final_score = int(base_score * 0.5)
        else:
            # Job didn't ask for any skills, fallback perfectly safely
            final_score = base_score
                
        # 4. Critical UI Formatting and Payload Filtering
        # Format the worker and map exactly what the frontend requires natively.
        worker['final_match_percentage'] = final_score
        worker['match_score'] = final_score
        
        # (is_requested and distance_km are already handled inside backend/routes/jobs.py wrapper)
        
        # ONLY APPEND WORKERS WHO PASS THE THRESHOLD
        if final_score >= 50:
            matched_workers.append(worker)

    # 5. Sort the list descending organically using the final score mapping keys
    matched_workers.sort(key=lambda x: x.get('final_match_percentage', 0), reverse=True)
    
    # 6. Debug print verifying exactly how many objects matched successfully
    print(f"DEBUG: Returning {len(matched_workers)} workers to frontend with match_percentage.", flush=True)

    return matched_workers

def basic_keyword_match(job_post, workers_list):
    return []