from appSwaggerTextLLMdb import app, db, ClinicalNote

with app.app_context():
    notes = ClinicalNote.query.all()
    if not notes:
        print("No records found.")
    for n in notes:
        print(f"[{n.id}] {n.timestamp} - {n.label}\n{n.note}\n")
