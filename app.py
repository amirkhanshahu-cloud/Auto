import os
import random
import time
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import cloudinary
import cloudinary.api

app = Flask(__name__)
app.secret_key = "jio_cloud_pro_secret_key"

cloudinary.config(
    cloud_name="dntmgunma",
    api_key="247386995162694",
    api_secret="Z4NDEGSgXqA5eUdNlRbjL6V-FoE"
)

WORKER_SECRET = "ATIF_PHONE_9988"

otp_store = {}
sms_queue = []
video_queue = []

BASE_STYLE = """
<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #0a0a0a; color: #fff; font-family: sans-serif; padding: 12px; }
    .header { background: #cc0000; padding: 15px; text-align: center; border-radius: 8px; margin-bottom: 14px; }
    .main-title { font-size: 20px; font-weight: bold; }
    .box { background: #141414; border: 1px solid #333; padding: 15px; margin-bottom: 15px; border-radius: 8px; }
    h3 { font-size: 16px; margin-bottom: 10px; color: #fff; }
    input[type="text"], input[type="tel"] { width: 100%; padding: 11px; margin: 6px 0 10px 0; background: #222; color: #fff; border: 1px solid #555; border-radius: 5px; font-size: 15px; }
    .btn { display: block; background: #cc0000; color: #fff; border: none; padding: 11px; font-weight: bold; border-radius: 5px; text-decoration: none; font-size: 15px; width: 100%; text-align: center; cursor: pointer; }
    .btn-green { background: #28a745; }
    .btn-dark { background: #2a2a2a; border: 1px solid #444; margin-top: 8px; }
    .msg { background: #2b2200; border: 1px solid #ffc107; color: #ffc107; padding: 9px; border-radius: 5px; font-size: 13px; margin-bottom: 12px; }
    
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }
    .card { background: #1b1b1b; border: 1px solid #2e2e2e; border-radius: 8px; overflow: hidden; }
    .card video { width: 100%; height: 140px; background: #000; }
    .card-body { padding: 8px; }
    .card-title { font-size: 13px; font-weight: bold; color: #fff; word-break: break-word; }
    .card-meta { font-size: 11px; color: #aaa; margin-top: 4px; }
    
    .pagination { text-align: center; margin-top: 16px; }
    .page-btn { display: inline-block; background: #222; border: 1px solid #444; color: #fff; padding: 8px 14px; text-decoration: none; border-radius: 5px; font-size: 13px; margin: 0 5px; }
</style>
"""

MAIN_HTML = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Jio Video Cloud Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {BASE_STYLE}
</head>
<body>
    <div class="header">
        <div class="main-title">Jio Video Cloud Pro</div>
    </div>

    {{% if msg %}}<div class="msg">{{{{ msg }}}}</div>{{% endif %}}

    {{% if verified %}}
    <div class="box">
        <h3>Video Upload / Request Karein</h3>
        <form action="/request_video" method="POST">
            <input type="text" name="query" placeholder="Video ka naam likhein..." required>
            <input type="submit" value="Download & Upload to Cloud" class="btn">
        </form>
    </div>
    {{% else %}}
    <div class="box">
        <h3>Mobile Verification</h3>
        <form action="/send_otp" method="POST">
            <input type="tel" name="phone" placeholder="Apna Mobile Number Dalein (e.g. 6387982416)" required>
            <input type="submit" value="OTP Bhejein" class="btn">
        </form>
    </div>
    {{% endif %}}

    <div class="box">
        <h3>Cloud Videos ({{{{ total_videos }}}})</h3>
        <a href="/?page={{{{ page }}}}" class="btn btn-dark" style="margin-bottom:12px;">↻ Refresh Gallery</a>

        {{% if videos %}}
        <div class="grid">
            {{% for vid in videos %}}
            <div class="card">
                <video controls preload="metadata">
                    <source src="{{{{ vid.secure_url }}}}" type="video/mp4">
                </video>
                <div class="card-body">
                    <div class="card-title">{{{{ vid.public_id }}}}</div>
                    <div class="card-meta">{{{{ (vid.bytes / (1024*1024)) | round(1) }}}} MB | {{{{ vid.format | upper }}}}</div>
                </div>
            </div>
            {{% endfor %}}
        </div>

        <div class="pagination">
            {{% if page > 1 %}}<a href="/?page={{{{ page - 1 }}}}" class="page-btn">← Prev</a>{{% endif %}}
            <span style="font-size:13px;">Page {{{{ page }}}} of {{{{ total_pages }}}}</span>
            {{% if page < total_pages %}}<a href="/?page={{{{ page + 1 }}}}" class="page-btn">Next →</a>{{% endif %}}
        </div>
        {{% else %}}
            <p style="color:#888; font-size:13px;">Abhi koi video upload nahi hui hai.</p>
        {{% endif %}}
    </div>
</body>
</html>
"""

OTP_HTML = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Verify OTP - Jio Video Cloud Pro</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {BASE_STYLE}
</head>
<body>
    <div class="header">
        <div class="main-title">Jio Video Cloud Pro</div>
    </div>

    {{% if msg %}}<div class="msg">{{{{ msg }}}}</div>{{% endif %}}

    <div class="box">
        <h3>OTP Code Dalein</h3>
        <p style="font-size:13px; color:#ccc; margin-bottom:10px;">Mobile: <b>{{{{ phone }}}}</b> par code bheja gaya hai.</p>
        <form action="/verify_otp" method="POST">
            <input type="hidden" name="phone" value="{{{{ phone }}}}">
            <input type="text" name="otp" placeholder="4-Digit OTP Dalein" required>
            <input type="submit" value="Verify Code" class="btn btn-green">
        </form>
        <a href="/" class="btn btn-dark">← Wapas Jayein</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    verified = session.get('verified', False)
    msg = request.args.get('msg', '')
    page = max(1, int(request.args.get('page', 1)))
    per_page = 20
    all_videos = []

    try:
        next_cursor = None
        while True:
            params = {"type": "upload", "resource_type": "video", "max_results": 100}
            if next_cursor:
                params["next_cursor"] = next_cursor
            res = cloudinary.api.resources(**params)
            all_videos.extend(res.get('resources', []))
            next_cursor = res.get('next_cursor')
            if not next_cursor:
                break
    except Exception as e:
        print("Cloudinary Fetch Error:", e)

    total_videos = len(all_videos)
    total_pages = max(1, (total_videos + per_page - 1) // per_page)
    page = min(page, total_pages)
    
    start = (page - 1) * per_page
    paginated_videos = all_videos[start:start + per_page]

    return render_template_string(
        MAIN_HTML,
        verified=verified,
        msg=msg,
        videos=paginated_videos,
        page=page,
        total_pages=total_pages,
        total_videos=total_videos
    )

@app.route('/send_otp', methods=['POST'])
def send_otp():
    phone = request.form.get('phone', '').strip()
    if len(phone) < 10:
        return redirect(url_for('index', msg="Sahi 10-digit mobile number dalein!"))
    code = str(random.randint(1000, 9999))
    otp_store[phone] = code
    sms_queue.append({"phone": phone, "otp": code})
    return render_template_string(OTP_HTML, phone=phone, msg="OTP bhej diya gaya hai, neeche code dalein.")

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    phone = request.form.get('phone', '').strip()
    otp = request.form.get('otp', '').strip()
    if otp_store.get(phone) == otp:
        session['verified'] = True
        del otp_store[phone]
        return redirect(url_for('index', msg="OTP Verify ho gaya! Ab video ka naam dalein."))
    return render_template_string(OTP_HTML, phone=phone, msg="Galat OTP! Dobara sahi code dalein.")

@app.route('/request_video', methods=['POST'])
def request_video():
    if not session.get('verified'):
        return redirect(url_for('index', msg="Pehle OTP verify karein!"))
    query = request.form.get('query', '').strip()
    if not query:
        return redirect(url_for('index', msg="Video ka naam likhein!"))
    video_queue.append({"id": int(time.time()), "query": query})
    return redirect(url_for('index', msg=f"'{query}' queue me lag gaya hai! Thodi der me Refresh karein."))

@app.route('/worker/get_tasks', methods=['GET'])
def get_tasks():
    if request.args.get('key') != WORKER_SECRET:
        return jsonify({"error": "Unauthorized"}), 403
    sms_task = sms_queue.pop(0) if sms_queue else None
    vid_task = video_queue.pop(0) if video_queue else None
    return jsonify({"sms": sms_task, "video": vid_task})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
