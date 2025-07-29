from flask import Flask, request, jsonify
import nibabel as nib
import numpy as np
import io

app = Flask(__name__)

# Global variables to store uploaded image and mask
uploaded_image = None
segmentation_mask = None
voxel_volume_mm3 = None  # voxel size in mm^3

def dummy_segmentation(image_data):
    """
    Dummy segmentation function:
    For demo, mark all voxels above a threshold as foreground
    """
    threshold = image_data.mean()  # just a simple threshold
    mask = (image_data > threshold).astype(np.uint8)
    return mask

@app.route('/')
def index():
    return "MRI API is running. Use endpoints /upload (POST), /segment (POST), /calculate-volume (GET), /status (GET)."

# @app.route('/upload', methods=['POST'])
# def upload_image():
#     global uploaded_image, voxel_volume_mm3
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"}), 400
    
#     file = request.files['file']
#     if file.filename == '':
#         return jsonify({"error": "No selected file"}), 400

#     # Read NIfTI file from bytes
#     file_bytes = file.read()
#     file_obj = io.BytesIO(file_bytes)
#     try:
#         nii = nib.load(file_obj)
#         uploaded_image = nii.get_fdata()
#         header = nii.header
#         # Calculate voxel volume in mm^3 from header pixdim
#         pixdim = header.get_zooms()[:3]  # voxel spacing along x,y,z
#         voxel_volume_mm3 = np.prod(pixdim)
#     except Exception as e:
#         return jsonify({"error": f"Failed to load NIfTI file: {str(e)}"}), 400

#     return jsonify({"message": f"Image uploaded successfully. Shape: {uploaded_image.shape}"}), 200

import tempfile
import os

@app.route('/upload', methods=['POST'])
def upload_image():
    global uploaded_image, voxel_volume_mm3

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # Now load with nibabel from actual file path
        nii = nib.load(tmp_path)
        uploaded_image = nii.get_fdata()
        header = nii.header
        pixdim = header.get_zooms()[:3]
        voxel_volume_mm3 = np.prod(pixdim)

        # Clean up temp file
        os.remove(tmp_path)

    except Exception as e:
        return jsonify({"error": f"Failed to load NIfTI file: {str(e)}"}), 400

    return jsonify({"message": f"Image uploaded successfully. Shape: {uploaded_image.shape}"}), 200



@app.route('/segment', methods=['POST'])
def segment():
    global uploaded_image, segmentation_mask
    if uploaded_image is None:
        return jsonify({"error": "No image uploaded"}), 400

    # Run dummy segmentation
    segmentation_mask = dummy_segmentation(uploaded_image)
    return jsonify({"message": "Segmentation completed"}), 200

@app.route('/calculate-volume', methods=['GET'])
def calculate_volume():
    global segmentation_mask, voxel_volume_mm3
    if segmentation_mask is None:
        return jsonify({"error": "No segmentation mask found"}), 400

    # Calculate volume in cubic millimeters and convert to cubic centimeters
    voxel_count = np.sum(segmentation_mask)
    volume_mm3 = voxel_count * voxel_volume_mm3
    volume_cm3 = volume_mm3 / 1000  # 1 cm3 = 1000 mm3

    return jsonify({"volume_cm3": volume_cm3, "voxel_count": int(voxel_count)}), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({"status": "API is running"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5062, debug=True)


# ---------------------------------------------
# (jupyter-env) [m254629@rohpc10 flask]$ python app.py
#  * Serving Flask app 'app'
#  * Debug mode: on
# WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
#  * Running on all addresses (0.0.0.0)
#  * Running on http://127.0.0.1:5062
#  * Running on http://10.128.217.9:5062
# Press CTRL+C to quit
#  * Restarting with watchdog (inotify)
#  * Debugger is active!
#  * Debugger PIN: 715-340-527
# 10.132.228.151 - - [08/Jul/2025 23:41:22] "GET / HTTP/1.1" 200 -
# 10.132.228.151 - - [08/Jul/2025 23:41:22] "GET /favicon.ico HTTP/1.1" 404 -
# Running on all addresses (0.0.0.0)
#  * Running on http://127.0.0.1:5062
#  * Running on http://10.128.217.9:5062
# Press CTRL+C to quit
#  * Restarting with watchdog (inotify)
#  * Debugger is active!
#  * Debugger PIN: 715-340-527
# ---------------------------------------------

# ---------------------------------------------
# Same commandline fire below lines
# ---------------------------------------------

# curl -X POST -F "file=@Axial.nii.gz" http://10.128.217.9:5062/upload
# curl -X POST http://10.128.217.9:5062/segment
# curl http://10.128.217.9:5062/calculate-volume

