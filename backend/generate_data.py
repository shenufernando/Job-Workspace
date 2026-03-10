import pandas as pd
import random

# 1. Create data (Data Lists)
job_types = [
    {"title": "Plumber", "skills": ["Pipe fitting", "Leak repair", "Water systems", "Bathroom installation"], "desc": "Fixing water leaks and installing pipes."},
    {"title": "Electrician", "skills": ["House wiring", "Panel board", "Lighting", "Electrical safety"], "desc": "Certified electrician for residential wiring."},
    {"title": "Mason", "skills": ["Brick laying", "Plastering", "Concrete work", "Tiling"], "desc": "Experienced mason for house construction."},
    {"title": "Carpenter", "skills": ["Furniture making", "Wood carving", "Roofing", "Polishing"], "desc": "Skilled carpenter for furniture and roofing."},
    {"title": "Web Developer", "skills": ["Python", "JavaScript", "React", "HTML/CSS", "Flask"], "desc": "Full stack web developer for websites."},
    {"title": "Graphic Designer", "skills": ["Photoshop", "Illustrator", "Logo Design", "Branding"], "desc": "Creative designer for logos and banners."},
    {"title": "Driver", "skills": ["Heavy Vehicle", "Light Vehicle", "Navigation", "English Speaking"], "desc": "Reliable driver with valid license."},
    {"title": "Gardener", "skills": ["Landscaping", "Grass cutting", "Tree trimming", "Planting"], "desc": "Professional gardener for home gardens."},
    {"title": "AC Technician", "skills": ["AC Repair", "Gas filling", "Servicing", "Installation"], "desc": "Expert in Air Condition repair and service."},
    {"title": "Painter", "skills": ["Wall painting", "Putty application", "Color mixing", "Spray painting"], "desc": "House painter for interior and exterior."},
]

locations = [
    "Colombo", "Gampaha", "Kandy", "Galle", "Matara", "Kurunegala", 
    "Negombo", "Kalutara", "Nugegoda", "Battaramulla", "Dehiwala", 
    "Maharagama", "Homagama", "Panadura", "Wattala"
]

# 2. Create 500 data (Generate 500 Rows)
data = []

for i in range(500):
    job = random.choice(job_types)
    location = random.choice(locations)
    experience = random.randint(1, 15) # Between 1 and 15 years
    
    # Random selection of 2 or 3 skills
    selected_skills = ", ".join(random.sample(job["skills"], k=random.randint(2, 3)))
    
    # Creating the Worker Profile Text (the most important part for AI)
    # Ex: "Experienced Plumber in Colombo with Pipe fitting skills. 5 years exp."
    profile_text = f"Professional {job['title']} located in {location}. Skilled in {selected_skills}. {experience} years of working experience. {job['desc']}"

    data.append([
        job["title"],
        job["desc"],
        selected_skills,
        location,
        experience,
        profile_text
    ])

# 3. Creating a DataFrame and Saving it as CSV
df = pd.DataFrame(data, columns=["Job_Title", "Job_Description", "Skills_Required", "Location", "Experience_Years", "Worker_Profile_Text"])

# Save CSV
filename = "job_worker_dataset.csv"
df.to_csv(filename, index=False)

print(f"Success! '{filename}' created with 500 rows.")
print("Sample Data:")
print(df.head())