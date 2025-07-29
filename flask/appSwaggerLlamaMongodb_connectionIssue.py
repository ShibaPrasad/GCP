from flask import Flask, request, Response
from flask_restx import Api, Resource, Namespace, fields
from pymongo import MongoClient
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import certifi
import io
import csv

# === Flask App Setup ===
app = Flask(__name__)
api = Api(app, version='1.0', title='LLaMA2 Clinical Text API',
          description='Classify clinical notes using LLaMA2')
ns = Namespace('llama', description='Text classification endpoints')
api.add_namespace(ns)

# === MongoDB Setup ===
mongo_uri = "mongodb+srv://shibapkuanar:C85hBDmYWdLrbujq@cluster0.7iohjz5.mongodb.net/?retryWrites=true&w=majority&tls=true&appName=Cluster0"
client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
db = client["clinical_db"]
notes_collection = db["notes"]

# === LLaMA2 Model Load ===
model_name = "meta-llama/Llama-2-7b-chat-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")
model.eval()

# === Swagger Models ===
classification_input = ns.model('ClinicalNote', {
    'note': fields.String(required=True, description='Clinical note text')
})

classification_output = ns.model('ClassificationResult', {
    'note': fields.String(description='Original note'),
    'label': fields.String(description='Predicted label'),
    'raw_output': fields.String(description='LLaMA2 full output'),
    'timestamp': fields.DateTime(description='Time of classification')
})

# === Prompt Template ===
def create_prompt(note):
    return f"""### Instruction:
Classify the following clinical note into one of the categories: Infection, Surgery, Equipment issue, or Other.

### Note:
{note}

### Response:
"""

# === Classification Endpoint ===
@ns.route('/classify')
class Classify(Resource):
    @ns.expect(classification_input)
    @ns.marshal_with(classification_output)
    def post(self):
        data = request.json
        note = data['note']
        prompt = create_prompt(note)

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=50, temperature=0.3)
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
        label = decoded.split("### Response:")[-1].strip().split("\n")[0]

        doc = {
            "note": note,
            "label": label,
            "raw_output": decoded,
            "timestamp": datetime.utcnow()
        }
        notes_collection.insert_one(doc)
        return doc

# === View Records (Optionally Filter by Label) ===
@ns.route('/records')
class Records(Resource):
    @ns.marshal_list_with(classification_output)
    def get(self):
        """Get all classification results or filter by label (?label=Infection)"""
        label_filter = request.args.get("label")
        query = {}
        if label_filter:
            query["label"] = {"$regex": f"^{label_filter}$", "$options": "i"}  # case-insensitive
        records = list(notes_collection.find(query, {"_id": 0}).sort("timestamp", -1))
        return records

# === Export Records to CSV ===
@ns.route('/export')
class Export(Resource):
    def get(self):
        """Export classification records as CSV"""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["note", "label", "timestamp", "raw_output"])
        writer.writeheader()
        for doc in notes_collection.find({}, {"_id": 0}).sort("timestamp", -1):
            writer.writerow(doc)
        output.seek(0)
        return Response(output, mimetype="text/csv", headers={
            "Content-Disposition": "attachment; filename=clinical_notes.csv"
        })

# === Optional: Seed Some Example Notes ===
def seed_test_notes():
    if notes_collection.count_documents({}) == 0:
        examples = [
            "Patient developed fever and chills 2 days after catheter insertion.",
            "Surgical drain was accidentally pulled out during patient repositioning.",
            "Patient is stable with no complaints during rounds.",
            "Chest x-ray shows consolidation in right lower lobe. Suspect pneumonia."
        ]
        for note in examples:
            prompt = create_prompt(note)
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(**inputs, max_new_tokens=50, temperature=0.3)
            decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
            label = decoded.split("### Response:")[-1].strip().split("\n")[0]
            notes_collection.insert_one({
                "note": note,
                "label": label,
                "raw_output": decoded,
                "timestamp": datetime.utcnow()
            })

@app.route('/')
def index():
    return "Welcome to the LLaMA2 Clinical Text API. Use /llama/* endpoints."

if __name__ == '__main__':
    seed_test_notes()
    app.run(host='0.0.0.0', port=5069, debug=True)
