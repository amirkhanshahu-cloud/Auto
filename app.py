import os
import random
import time
from flask import Flask, request, jsonify, render_template_string, session
import cloudinary
import cloudinary.api

app = Flask(__name__)
app.secret_key = "super_secret_jio_cloud_key"

cloudinary.config(
    cloud_name="dntmgunma",
    api_key="247386995162694",
    api_secret="Z4NDEGSgXqA5eUdNlRbjL6V-FoE"
)

WORKER_SECRET = "ATIF_PHONE_9988"

otp_store = {}
sms_queue = []
video_queue = []

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>Jio Video Cloud Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #000; color: #fff; font-family: sans-serif; padding: 10px; margin: 0; }
        .header { background: #cc0000; padding: 15px; text-align: center; border-radius: 5px; }
        .main-title { font-size: 20px; font-weight: bold; }
        .box { border: 2px dashed #444; padding: 15px; margin-top: 15px; border-radius: 8px; background: #111; }
        input[type="text"], input[type="tel"] { width: 92%; padding: 10px; margin: 8px 0; background: #222; color: #fff; border: 1px solid #555; border-radius: 4px; }
        button { background: #cc0000; color: #fff; border: none; padding: 10px 18px; font-weight: bold; border-radius: 4px; cursor: pointer; width: 100%; }
        .video-card { background: #1a1a1a; padding: 10px; margin-top: 12px; border-radius: 6px; border: 1px solid #333; }
        video { width: 100%; border-radius: 4px; margin-top: 5px; }
        .msg { color: #ffc107; font-size: 14px; margin-top: 8px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="main-title">Jio Video Cloud Pro</div>
    </div>

    {% if not verified %}
    <div class="box">
        <h3>1. Mobile Verification</h3>
        <input type="tel" id="phone" placeholder="Apna Mobile Number Dalein (e.g. 9876543210)">
        <button onclick="sendOTP()">OTP Bhejein</button>
        
        <div id="otp-section" style="display:none; margin-top:15px;">
            <input type="text" id="otp" placeholder="4-Digit OTP Dalein">
            <button onclick="verifyOTP()">Verify Code</button>
        </div>
        <div class="msg" id="auth-msg"></div>
    </div>
    {% else %}
    <div class="box">
        <h3>2. Video Request Karein</h3>
        <input type="text" id="vname" placeholder="Video ka naam likhein...">
        <button onclick="requestVideo()">Download & Upload to Cloud</button>
        <div class="msg" id="vid-msg"></div>
    </div>
    {% endif %}

    <div class="box">
        <h3>Cloud Videos (Auto-Split Supported)</h3>
        <button onclick="location.reload()" style="background:#333; margin-bottom:10px;">Refresh Gallery</button>
        {% for vid in videos %}
        <div class="video-card">
            <div><strong>{{ vid.public_id }}</strong> ({{ (vid.bytes / (1024*1024)) | round(1) }} MB)</div>
            <video controls preload="none">
                <source src="{{ vid.secure_url }}" type="video/mp4">
            </video>
        </div>
        {% endfor %}
    </div>

    <script>
        function sendOTP() {
            let phone = document.getElementById('phone').value;
            fetch('/send_otp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone: phone})
            }).then(r => r.json()).then(d => {
                document.getElementById('auth-msg').innerText = d.message;
                if(d.success) document.getElementById('otp-section').style.display = 'block';
            });
        }
        function verifyOTP() {
            let phone = document.getElementById('phone').value;
            let otp = document.getElementById('otp').value;
            fetch('/verify_otp', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({phone: phone, otp: otp})
            }).then(r => r.json()).then(d => {
                document.getElementById('auth-msg').innerText = d.message;
                if(d.success) location.reload();
            });
        }
        function requestVideo() {
            let query = document.getElementById('vname').value;
            fetch('/request_video', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({query: query})
            }).then(r => r.json()).then(d => {
                document.getElementById('vid-msg').innerText = d.message;
                document.getElementById('vname').value = '';
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    verified = session.get('verified', False)
    videos = []
    try:
        res = cloudinary.api.resources(type="upload", resource_type="video", max_results=30)
        videos = res.get('resources', [])
    except Exception as e:
        print("Cloudinary Fetch Error:", e)
    return render_template_string(HTML_PAGE, verified=verified, videos=videos)

@app.route('/send_otp', methods=['POST'])
def send_otp():
    phone = request.json.get('phone', '').strip()
    if len(phone) < 10:
        return jsonify({"success": False, "message": "Sahi mobile number dalein!"})
    code = str(random.randint(1000, 9999))
    otp_store[phone] = code
    sms_queue.append({"phone": phone, "otp": code})
    return jsonify({"success": True, "message": "Phone server se OTP bheja ja raha hai..."})

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    phone = request.json.get('phone', '').strip()
    otp = request.json.get('otp', '').strip()
    if otp_store.get(phone) == otp:
        session['verified'] = True
        del otp_store[phone]
        return jsonify({"success": True, "message": "Verified!"})
    return jsonify({"success": False, "message": "Galat OTP! Dobara check karein."})

@app.route('/request_video', methods=['POST'])
def request_video():
    if not session.get('verified'):
        return jsonify({"success": False, "message": "Pehle OTP verify karein!"})
    query = request.json.get('query', '').strip()
    if not query:
        return jsonify({"success": False, "message": "Video ka naam likhein!"})
    video_queue.append({"id": int(time.time()), "query": query})
    return jsonify({"success": True, "message": f"'{query}' queue me lag gaya hai. Phone download karke seedha Cloud par upload karega!"})

@app.route('/worker/get_tasks', methods=['GET'])
def get_tasks():
    if request.args.get('key') != WORKER_SECRET:
        return jsonify({"error": "Unauthorized"}), 403
    
    sms_task = sms_queue.pop(0) if sms_queue else None
    vid_task = video_queue.pop(0) if video_queue else None
    return jsonify({"sms": sms_task, "video": vid_task})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
