from flask import Flask, request
from flask_restx import Api, Resource, Namespace, fields
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# Initialize Flask app
app = Flask(__name__)
api = Api(app, version='1.0', title='Clinical Note Classifier API',
          description='Upload clinical note text and get classification using LLaMA2')

ns = Namespace('llama', description='LLaMA2 Clinical Text Classification')
api.add_namespace(ns)

# Input schema for Swagger UI
classification_input = ns.model('ClinicalNote', {
    'note': fields.String(required=True, description='Clinical note text')
})

# Output schema
classification_output = ns.model('ClassificationResult', {
    'label': fields.String(description='Predicted classification label'),
    'raw_output': fields.String(description='Raw model response (optional)')
})

# Load LLaMA2 tokenizer and model (adjust path or HF model name as needed)
model_name = "meta-llama/Llama-2-7b-chat-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map='auto')
model.eval()

# Prompt template
def create_prompt(clinical_note):
    return f"""### Instruction:
Classify the following clinical note into one of the categories: Infection, Surgery, Equipment issue, or Other.

### Note:
{clinical_note}

### Response:
"""

@ns.route('/classify')
class Classify(Resource):
    @ns.expect(classification_input)
    @ns.marshal_with(classification_output)
    def post(self):
        """
        Classify a clinical note using LLaMA2

        Example Input:
        {
            "note": "Patient underwent laparoscopic cholecystectomy for gallbladder removal. Post-operative course was complicated by signs of infection including elevated WBC count and fever. Blood cultures were ordered. Antibiotics were initiated empirically."
        }

        Example Output:
        {
            "label": "Infection",
            "raw_output": "Infection"
        }
        """
        data = request.json
        note = data['note']
        prompt = create_prompt(note)

        # Tokenize and generate
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=50, temperature=0.3)
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract label
        response_text = decoded.split("### Response:")[-1].strip().split("\n")[0]
        return {'label': response_text, 'raw_output': decoded}


@ns.route('/status')
class Status(Resource):
    def get(self):
        """Check API status"""
        return {"status": "LLaMA2 Clinical Text Classification API is running"}, 200


@app.route('/')
def index():
    return "Go to / to view Swagger UI or use /llama/* endpoints."


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5065, debug=True)
