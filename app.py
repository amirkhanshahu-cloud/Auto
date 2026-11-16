import os
import random
import time
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import cloudinary
import cloudinary.api

app = Flask(__name__)
app.secret_key = "jio_cloud_pro_secret_key"

# Cloudinary Config
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
    body { background: #0a0a0a; color: #fff; font-family: sans-serif; padding: 10px; margin: 0; }
    .header { background: #cc0000; padding: 14px; text-align: center; border-radius: 6px; margin-bottom: 12px; }
    .main-title { font-size: 20px; font-weight: bold; }
    .box { background: #141414; border: 1px solid #333; padding: 14px; margin-bottom: 14px; border-radius: 8px; }
    h3 { font-size: 16px; margin: 0 0 10px 0; color: #fff; }
    input[type="text"], input[type="tel"] { width: 94%; padding: 10px; margin: 6px 0 10px 0; background: #222; color: #fff; border: 1px solid #555; border-radius: 5px; font-size: 15px; }
    .btn { display: inline-block; background: #cc0000; color: #fff; border: none; padding: 11px 16px; font-weight: bold; border-radius: 5px; text-decoration: none; font-size: 14px; width: 100%; text-align: center; cursor: pointer; }
    .btn-green { background: #28a745; }
    .btn-dark { background: #2a2a2a; border: 1px solid #444; width: auto; padding: 8px 14px; }
    .msg { background: #2b2200; border: 1px solid #ffc107; color: #ffc107; padding: 8px; border-radius: 5px; font-size: 13px; margin-bottom: 10px; }
    
    /* Lightweight Card Layout for Opera Mini & Low-end Phones */
    .card { background: #1b1b1b; border: 1px solid #2e2e2e; border-radius: 6px; padding: 10px; margin-bottom: 12px; }
    .card video { width: 100%; max-height: 200px; background: #000; border-radius: 4px; }
    .card-title { font-size: 14px; font-weight: bold; margin-top: 6px; word-wrap: break-word; }
    .card-meta { font-size: 12px; color: #aaa; margin-top: 4px; }
    .dl-link { display: inline-block; margin-top: 6px; color: #4da6ff; font-size: 13px; text-decoration: none; font-weight: bold; }
    
    .pagination { text-align: center; margin-top: 14px; }
    .page-btn { display: inline-block; background: #222; border: 1px solid #444; color: #fff; padding: 8px 14px; text-decoration: none; border-radius: 5px; font-size: 13px; margin: 0 5px; }
</style>
"""

HOME_HTML = f"""
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
        <h3>Verified: {{{{ verified_phone }}}}</h3>
        <a href="/request" class="btn btn-green">+ Nayi Video Request Karein</a>
    </div>
    {{% else %}}
    <div class="box">
        <h3>Step 1: Mobile Verification</h3>
        <form action="/send_otp" method="POST">
            <input type="tel" name="phone" placeholder="Mobile Number (e.g. 6387982416)" required>
            <button type="submit" class="btn">OTP Bhejein →</button>
        </form>
    </div>
    {{% endif %}}

    <div class="box">
        <h3>Cloud Videos ({{{{ total_videos }}}}) <a href="/?page={{{{ page }}}}" class="btn btn-dark" style="float:right;">↻ Refresh</a></h3>
        <div style="clear:both; margin-bottom:10px;"></div>

        {{% if videos %}}
            {{% for vid in videos %}}
            <div class="card">
                <video controls preload="none">
                    <source src="{{{{ vid.secure_url }}}}" type="video/mp4">
                </video>
                <div class="card-title">{{{{ vid.public_id }}}}</div>
                <div class="card-meta">Size: {{{{ (vid.bytes / (1024*1024)) | round(1) }}}} MB | Format: {{{{ vid.format | upper }}}}</div>
                <a href="{{{{ vid.secure_url }}}}" class="dl-link" download>⬇ Direct Download MP4</a>
            </div>
            {{% endfor %}}

            <div class="pagination">
                {{% if page > 1 %}}<a href="/?page={{{{ page - 1 }}}}" class="page-btn">← Prev</a>{{% endif %}}
                <span style="font-size:13px;">Page {{{{ page }}}} / {{{{ total_pages }}}}</span>
                {{% if page < total_pages %}}<a href="/?page={{{{ page + 1 }}}}" class="page-btn">Next →</a>{{% endif %}}
            </div>
        {{% else %}}
            <p style="color:#888; font-size:13px;">Abhi koi video nahi hai.</p>
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
    <title>Verify OTP - Jio Video Cloud</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {BASE_STYLE}
</head>
<body>
    <div class="header">
        <div class="main-title">OTP Verification</div>
    </div>

    {{% if msg %}}<div class="msg">{{{{ msg }}}}</div>{{% endif %}}

    <div class="box">
        <h3>Step 2: Code Dalein</h3>
        <p style="font-size:13px; color:#ccc; margin-bottom:10px;">Number: <b>{{{{ phone }}}}</b> par SMS bheja gaya hai.</p>
        <form action="/verify_otp" method="POST">
            <input type="hidden" name="phone" value="{{{{ phone }}}}">
            <input type="text" name="otp" placeholder="4-Digit OTP Code Dalein" required>
            <button type="submit" class="btn btn-green">Verify OTP →</button>
        </form>
        <br>
        <a href="/" style="color:#aaa; font-size:13px; text-decoration:none;">← Number Badlein</a>
    </div>
</body>
</html>
"""

REQUEST_HTML = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Request Video - Jio Video Cloud</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {BASE_STYLE}
</head>
<body>
    <div class="header">
        <div class="main-title">Video Request</div>
    </div>

    {{% if msg %}}<div class="msg">{{{{ msg }}}}</div>{{% endif %}}

    <div class="box">
        <h3>Step 3: Video Ka Naam Likhein</h3>
        <p style="font-size:12px; color:#aaa; margin-bottom:8px;">Video 240p me download hokar seedha Cloud gallery me upload hogi.</p>
        <form action="/request_video" method="POST">
            <input type="text" name="query" placeholder="Video ka naam likhein..." required>
            <button type="submit" class="btn">Download & Upload Karein</button>
        </form>
        <br>
        <a href="/" class="btn btn-dark" style="width:90%; display:block;">← Cloud Gallery Dekhein</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    verified = session.get('verified', False)
    verified_phone = session.get('phone', '')
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
        HOME_HTML,
        verified=verified,
        verified_phone=verified_phone,
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
    return render_template_string(OTP_HTML, phone=phone, msg="OTP SMS bhej diya gaya hai, neeche code dalein.")

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    phone = request.form.get('phone', '').strip()
    otp = request.form.get('otp', '').strip()
    if otp_store.get(phone) == otp:
        session['verified'] = True
        session['phone'] = phone
        del otp_store[phone]
        return redirect(url_for('request_page', msg="OTP Verify ho gaya! Ab video ka naam dalein."))
    return render_template_string(OTP_HTML, phone=phone, msg="Galat OTP! Dobara sahi code dalein.")

@app.route('/request', methods=['GET'])
def request_page():
    if not session.get('verified'):
        return redirect(url_for('index', msg="Pehle mobile number verify karein!"))
    msg = request.args.get('msg', '')
    return render_template_string(REQUEST_HTML, msg=msg)

@app.route('/request_video', methods=['POST'])
def request_video():
    if not session.get('verified'):
        return redirect(url_for('index', msg="Pehle OTP verify karein!"))
    query = request.form.get('query', '').strip()
    if not query:
        return redirect(url_for('request_page', msg="Video ka naam likhein!"))
    video_queue.append({"id": int(time.time()), "query": query})
    return redirect(url_for('index', msg=f"'{query}' download ke liye lag gaya hai! 1-2 minute baad Refresh karein."))

@app.route('/worker/get_tasks', methods=['GET'])
def get_tasks():
    if request.args.get('key') != WORKER_SECRET:
        return jsonify({"error": "Unauthorized"}), 403
    sms_task = sms_queue.pop(0) if sms_queue else None
    vid_task = video_queue.pop(0) if video_queue else None
    return jsonify({"sms": sms_task, "video": vid_task})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
