from flask import Flask, request, Response, send_file
from flask_restx import Api, Resource, Namespace, fields, reqparse
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.datastructures import FileStorage
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

from flask_cors import CORS
app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clinical_notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

api = Api(app, version='1.0', title='Clinical Note Classifier API',
          description='Upload clinical notes and get classification using LLaMA2')
ns = Namespace('llama', description='LLaMA2 Clinical Text Classification')
api.add_namespace(ns)

# === Model Setup ===
model_name = "meta-llama/Llama-2-7b-chat-hf"
try:
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_auth_token=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto",
        use_auth_token=True
    )
    model.eval()
except Exception as e:
    print(f"Failed to load model: {e}")
    tokenizer = None
    model = None

# === DB Model ===
class ClinicalNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mrn = db.Column(db.String(20))
    department = db.Column(db.String(50))
    event_date = db.Column(db.Date)
    note = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(50))
    ground_truth = db.Column(db.String(50))
    raw_output = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# === Swagger Schemas ===
classification_input = ns.model('ClinicalNote', {
    'note': fields.String(required=True, description='Clinical note text')
})

classification_output = ns.model('ClassificationResult', {
    'id': fields.Integer,
    'mrn': fields.String,
    'department': fields.String,
    'event_date': fields.String,
    'note': fields.String,
    'label': fields.String,
    'ground_truth': fields.String,
    'timestamp': fields.DateTime,
    'raw_output': fields.String
})

upload_model = ns.model('UploadSummary', {
    'processed': fields.Integer,
    'success': fields.Integer,
    'failed': fields.Integer
})

def create_prompt(note):
    return f"""### Instruction:
Classify the following clinical note into one of the categories: Infection, Surgery, Equipment issue, or Other.

### Note:
{note}

### Response:
"""

@ns.route('/classify')
class Classify(Resource):
    @ns.expect(classification_input)
    @ns.marshal_with(classification_output)
    def post(self):
        if model is None or tokenizer is None:
            ns.abort(500, "Model not loaded. Check server logs.")

        try:
            data = request.json
            note = data['note']

            prompt = create_prompt(note)
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            outputs = model.generate(**inputs, max_new_tokens=50, temperature=0.3)
            decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
            label = decoded.split("### Response:")[-1].strip().split("\n")[0].strip()

            record = ClinicalNote(note=note, label=label, raw_output=decoded)
            db.session.add(record)
            db.session.commit()

            return record
        except Exception as e:
            print("Classification error:", str(e))
            ns.abort(500, f"Classification error: {str(e)}")

@ns.route('/records')
class GetRecords(Resource):
    @ns.marshal_list_with(classification_output)
    def get(self):
        return ClinicalNote.query.order_by(ClinicalNote.timestamp.desc()).all()

@ns.route('/export')
class ExportCSV(Resource):
    def get(self):
        notes = ClinicalNote.query.order_by(ClinicalNote.timestamp.desc()).all()
        data = [{
            'id': n.id,
            'mrn': n.mrn,
            'department': n.department,
            'event_date': n.event_date.isoformat() if n.event_date else None,
            'note': n.note,
            'label': n.label,
            'ground_truth': n.ground_truth,
            'timestamp': n.timestamp.isoformat(),
            'raw_output': n.raw_output
        } for n in notes]

        df = pd.DataFrame(data)
        return Response(
            df.to_csv(index=False),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=classification_results.csv"}
        )

upload_parser = reqparse.RequestParser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=True, help='CSV with MRN, Note, Department, EventDate[, GroundTruth]')

@ns.route('/upload')
class UploadCSV(Resource):
    @ns.expect(upload_parser)
    @ns.marshal_with(upload_model)
    def post(self):
        args = upload_parser.parse_args()
        uploaded_file = args['file']

        if not uploaded_file or not uploaded_file.filename.endswith('.csv'):
            ns.abort(400, 'Only .csv files are supported.')

        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            ns.abort(400, f"Failed to parse CSV: {str(e)}")

        required_cols = {"MRN", "Note", "Department", "EventDate"}
        if not required_cols.issubset(df.columns):
            ns.abort(400, f"CSV must include columns: {required_cols}")

        has_gt = "GroundTruth" in df.columns
        success, failed = 0, 0

        for _, row in df.iterrows():
            try:
                note = row["Note"]
                prompt = create_prompt(note)
                inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
                outputs = model.generate(**inputs, max_new_tokens=50, temperature=0.3)
                decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
                label = decoded.split("### Response:")[-1].strip().split("\n")[0].strip()

                record = ClinicalNote(
                    mrn=str(row["MRN"]),
                    department=row["Department"],
                    event_date=pd.to_datetime(row["EventDate"]).date(),
                    note=note,
                    label=label,
                    ground_truth=row["GroundTruth"] if has_gt else None,
                    raw_output=decoded
                )
                db.session.add(record)
                success += 1
            except Exception as e:
                print(f"Failed on row: {e}")
                failed += 1

        db.session.commit()
        return {'processed': len(df), 'success': success, 'failed': failed}

@ns.route('/analytics')
class Analytics(Resource):
    def get(self):
        notes = ClinicalNote.query.all()
        if not notes:
            ns.abort(404, "No data available for analytics.")

        df = pd.DataFrame([{
            'label': n.label,
            'ground_truth': n.ground_truth,
            'event_date': n.event_date,
            'department': n.department
        } for n in notes])
        df.dropna(subset=['label', 'event_date', 'department'], inplace=True)

        sns.set(style="whitegrid")
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        plt.subplots_adjust(hspace=0.5, wspace=0.3)

        sns.countplot(x='label', data=df, ax=axes[0, 0], palette='pastel')
        axes[0, 0].set_title('Label Distribution')
        axes[0, 0].set_ylabel('Count')

        df_by_date = df.groupby(df['event_date'].astype(str)).size()
        df_by_date.plot(kind='line', marker='o', ax=axes[0, 1])
        axes[0, 1].set_title('Events Over Time')
        axes[0, 1].set_ylabel('Count')
        axes[0, 1].tick_params(axis='x', rotation=45)

        sns.countplot(y='department', hue='label', data=df, ax=axes[1, 0], palette='Set2')
        axes[1, 0].set_title('Department-wise Classification')

        if df['ground_truth'].notna().sum() > 0:
            gt_df = df.dropna(subset=['ground_truth'])
            labels = sorted(set(gt_df['ground_truth']).union(set(gt_df['label'])))
            acc = accuracy_score(gt_df['ground_truth'], gt_df['label'])

            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                        xticklabels=sorted(set(gt_df['label'])),
                        yticklabels=sorted(set(gt_df['ground_truth'])),
                        ax=axes[1, 1])
            axes[1, 1].set_title(f'Confusion Matrix (Accuracy = {acc:.2f})')
            axes[1, 1].set_xlabel('Predicted')
            axes[1, 1].set_ylabel('Ground Truth')
        else:
            axes[1, 1].axis('off')
            axes[1, 1].text(0.5, 0.5, 'No ground truth available', fontsize=12,
                            ha='center', va='center', transform=axes[1, 1].transAxes)

        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return send_file(buf, mimetype='image/png', as_attachment=False, download_name='analytics.png')

@ns.route('/metrics')
class MetricsCSV(Resource):
    def get(self):
        notes = ClinicalNote.query.filter(ClinicalNote.ground_truth.isnot(None)).all()
        if not notes:
            ns.abort(404, "No records with ground truth available.")

        y_true = [n.ground_truth for n in notes]
        y_pred = [n.label for n in notes]

        report_dict = classification_report(y_true, y_pred, output_dict=True)
        df_report = pd.DataFrame(report_dict).transpose()

        if 'accuracy' not in df_report.index:
            acc = accuracy_score(y_true, y_pred)
            df_report.loc['accuracy'] = {
                'precision': acc,
                'recall': acc,
                'f1-score': acc,
                'support': len(y_true)
            }

        return Response(
            df_report.to_csv(index=True),
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=classification_metrics.csv"}
        )

@app.route("/")
def index():
    return "Visit / to use Swagger UI (http://localhost:5086/)."

@app.route("/ping", methods=["GET"])
def ping():
    return {"message": "Server is alive!"}, 200

@app.route("/health", methods=["GET"])
def health():
    return {
        "model_loaded": model is not None,
        "tokenizer_loaded": tokenizer is not None
    }, 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5086, debug=True, use_reloader=False)
