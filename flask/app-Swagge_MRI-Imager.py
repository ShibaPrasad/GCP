from flask import Flask, request
from flask_restx import Api, Resource, Namespace, fields
import nibabel as nib
import numpy as np
import tempfile
import os
from werkzeug.datastructures import FileStorage

app = Flask(__name__)
api = Api(app, version='1.0', title='MRI Segmentation API',
          description='Upload MRI, run segmentation, and calculate volume')

ns = Namespace('mri', description='MRI operations')
api.add_namespace(ns)

# Globals
uploaded_image = None
segmentation_mask = None
voxel_volume_mm3 = None

# Swagger models
upload_parser = ns.parser()
# upload_parser.add_argument('file', location='files', type='FileStorage', required=True)
upload_parser.add_argument('file', location='files', type=FileStorage, required=True)


volume_model = ns.model('Volume', {
    'volume_cm3': fields.Float(description='Calculated volume in cubic centimeters'),
    'voxel_count': fields.Integer(description='Number of segmented voxels')
})

status_model = ns.model('Status', {
    'status': fields.String(description='API status message')
})


# Dummy segmentation logic
def dummy_segmentation(image_data):
    threshold = image_data.mean()
    return (image_data > threshold).astype(np.uint8)


@ns.route('/upload')
@ns.expect(upload_parser)
class Upload(Resource):
    def post(self):
        """Upload NIfTI MRI file (.nii.gz)"""
        global uploaded_image, voxel_volume_mm3
        args = upload_parser.parse_args()
        file = args['file']

        if file.filename == '':
            return {"error": "No file selected"}, 400

        try:
            with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name

            nii = nib.load(tmp_path)
            uploaded_image = nii.get_fdata()
            voxel_volume_mm3 = np.prod(nii.header.get_zooms()[:3])
            os.remove(tmp_path)
        except Exception as e:
            return {"error": f"Failed to load NIfTI file: {str(e)}"}, 400

        return {"message": f"Image uploaded. Shape: {uploaded_image.shape}"}, 200


@ns.route('/segment')
class Segment(Resource):
    def post(self):
        """Run dummy segmentation on uploaded MRI"""
        global uploaded_image, segmentation_mask
        if uploaded_image is None:
            return {"error": "No image uploaded"}, 400
        segmentation_mask = dummy_segmentation(uploaded_image)
        return {"message": "Segmentation completed"}, 200


@ns.route('/calculate-volume')
class CalculateVolume(Resource):
    @ns.marshal_with(volume_model)
    def get(self):
        """Calculate volume of segmented region"""
        global segmentation_mask, voxel_volume_mm3
        if segmentation_mask is None:
            return {"error": "No segmentation available"}, 400
        voxel_count = int(np.sum(segmentation_mask))
        volume_cm3 = voxel_count * voxel_volume_mm3 / 1000
        return {"volume_cm3": volume_cm3, "voxel_count": voxel_count}, 200


@ns.route('/status')
class Status(Resource):
    @ns.marshal_with(status_model)
    def get(self):
        """Check API status"""
        return {"status": "MRI API is running"}, 200


@app.route('/')
def index():
    return "Go to / to view Swagger UI or use /mri/* endpoints."


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5064, debug=True)
