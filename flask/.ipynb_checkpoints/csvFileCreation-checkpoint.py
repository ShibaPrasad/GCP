import csv
import random
from datetime import datetime, timedelta

# Sample data components
departments = ['Surgery', 'ICU', 'ER', 'PrimaryCare', 'InfectiousDiseases', 'Radiology', 'Cardiology', 'Oncology']
labels = ['Infection', 'Surgery', 'Equipment issue', 'Other']

# Sample note templates per label (with placeholders)
note_templates = {
    'Infection': [
        "Patient developed fever and redness at the {site}.",
        "Signs of infection including elevated WBC and {symptom}.",
        "Localized swelling and pain indicating possible infection at {site}.",
        "Patient reports productive cough and chills, suspect respiratory infection.",
        "Redness and inflammation noted around {site}."
    ],
    'Surgery': [
        "Post-op day {day}: patient shows swelling and bruising near incision site.",
        "Patient recovering from surgery with no complications observed.",
        "Delayed wound healing observed after surgical procedure.",
        "Patient reports discomfort and minor bleeding at surgical site.",
        "Surgical site redness and drainage on post-op day {day}."
    ],
    'Equipment issue': [
        "Malfunctioning {equipment} caused interruption in treatment.",
        "Patient complains of discomfort due to {equipment} failure.",
        "Equipment error led to delayed medication delivery.",
        "Catheter leakage detected causing minor bleeding.",
        "IV pump malfunction resulted in interrupted infusion."
    ],
    'Other': [
        "Routine follow-up visit without complaints.",
        "Patient stable with no adverse symptoms reported.",
        "No safety events noted during current evaluation.",
        "Regular check-up showed no complications.",
        "Patient reports mild fatigue but no other issues."
    ]
}

# Possible sites and symptoms for infection notes
infection_sites = ['incision site', 'catheter insertion site', 'wound area', 'respiratory tract']
infection_symptoms = ['chills', 'body aches', 'fatigue']

# Possible equipment types
equipment_types = ['IV pump', 'catheter', 'ventilator', 'oxygen supply', 'monitoring device']

# Generate 100 entries
entries = []
start_date = datetime.strptime("2022-01-01", "%Y-%m-%d")

for i in range(1, 101):
    mrn = 1000 + i
    label = random.choice(labels)
    department = random.choice(departments)
    event_date = start_date + timedelta(days=random.randint(0, 900))
    event_date_str = event_date.strftime("%Y-%m-%d")

    # Create note based on label
    template = random.choice(note_templates[label])
    if label == 'Infection':
        site = random.choice(infection_sites)
        symptom = random.choice(infection_symptoms)
        note = template.format(site=site, symptom=symptom)
    elif label == 'Surgery':
        day = random.randint(1, 14)
        note = template.format(day=day)
    elif label == 'Equipment issue':
        equipment = random.choice(equipment_types)
        note = template.format(equipment=equipment)
    else:  # Other
        note = template

    entries.append({
        'MRN': mrn,
        'Note': note,
        'Department': department,
        'EventDate': event_date_str,
        'GroundTruth': label
    })

# Write to CSV
csv_filename = 'patient_safety_data.csv'
with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['MRN', 'Note', 'Department', 'EventDate', 'GroundTruth']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for entry in entries:
        writer.writerow(entry)

print(f"Generated {csv_filename} with 100 patient safety entries.")
