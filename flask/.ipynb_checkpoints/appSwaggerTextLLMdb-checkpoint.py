from flask import Flask, request
from flask_restx import Api, Resource, Namespace, fields
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


# === Flask + DB Setup ===
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinical_notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app, version='1.0', title='Clinical Note Classifier API',
          description='Upload clinical note text and get classification using LLaMA2')
ns = Namespace('llama', description='LLaMA2 Clinical Text Classification')
api.add_namespace(ns)

# === LLaMA2 Model Setup ===
model_name = "meta-llama/Llama-2-7b-chat-hf"  # Change if local or quantized
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map='auto')
model.eval()

# === DB Table ===
class ClinicalNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(50))
    raw_output = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# === Swagger Schemas ===
classification_input = ns.model('ClinicalNote', {
    'note': fields.String(required=True, description='Clinical note text')
})

classification_output = ns.model('ClassificationResult', {
    'id': fields.Integer(description='DB ID'),
    'note': fields.String(description='Clinical note'),
    'label': fields.String(description='Predicted label'),
    'timestamp': fields.DateTime,
    'raw_output': fields.String(description='Full LLaMA2 response')
})

# === Prompt Template ===
def create_prompt(note):
    return f"""### Instruction:
Classify the following clinical note into one of the categories: Infection, Surgery, Equipment issue, or Other.

### Note:
{note}

### Response:
"""

# === API Routes ===
@ns.route('/classify')
class Classify(Resource):
    @ns.expect(classification_input)
    @ns.marshal_with(classification_output)
    def post(self):
        """
        Classify a clinical note using LLaMA2 and store result in database.

        Example:
        {
            "note": "Patient presented with fever, elevated WBC, and redness at the incision site."
        }
        """
        data = request.json
        note = data['note']
        prompt = create_prompt(note)

        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=50, temperature=0.3)
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

        label = decoded.split("### Response:")[-1].strip().split("\n")[0]

        record = ClinicalNote(note=note, label=label, raw_output=decoded)
        db.session.add(record)
        db.session.commit()

        return {
            "id": record.id,
            "note": note,
            "label": label,
            "timestamp": record.timestamp,
            "raw_output": decoded
        }

@ns.route('/records')
class GetRecords(Resource):
    @ns.marshal_list_with(classification_output)
    def get(self):
        """Get all classified clinical notes from the database."""
        return ClinicalNote.query.order_by(ClinicalNote.timestamp.desc()).all()

@app.route('/')
def index():
    return "Go to / to view Swagger UI. Use /llama/classify to POST notes."

# === Main App Runner ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Load sample notes only if DB is empty
        if ClinicalNote.query.count() == 0:
            sample_notes = [
                "Patient developed redness and drainage at the surgical site on post-op day 3.",
                "The patient reports discomfort with catheter function and minor bleeding from the tube site.",
                "Routine follow-up visit without complaints. No adverse symptoms reported.",
                "Patient shows signs of respiratory infection including productive cough and fever."
            ]
            for note in sample_notes:
                prompt = create_prompt(note)
                inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
                outputs = model.generate(**inputs, max_new_tokens=50, temperature=0.3)
                decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
                label = decoded.split("### Response:")[-1].strip().split("\n")[0]
                db.session.add(ClinicalNote(note=note, label=label, raw_output=decoded))
            db.session.commit()

    app.run(host='0.0.0.0', port=5066, debug=True)
