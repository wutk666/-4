from flask import current_app, request, jsonify, render_template, redirect, url_for, flash, make_response, session
from .models import BannedIP, AttackLog, User, Setting, Comment, VulnerableUser, VulnerableFile, RateLimitLog
from . import db, login_manager
from flask_login import login_user, logout_user, login_required, current_user
import ipaddress
from datetime import datetime, timedelta
import os
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
import uuid
from .attack_detectors import AttackDetectorManager
from . import auth_security

# 允许上传的图片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp'}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _find_static_img_by_prefix(app, prefix: str):
    img_folder = os.path.join(app.root_path, 'static', 'img')
    if not os.path.exists(img_folder):
        return None
    candidates = []
    for ext in ALLOWED_EXTENSIONS:
        name = f"{prefix}.{ext}"
        p = os.path.join(img_folder, name)
        if os.path.exists(p):
            candidates.append((name, os.path.getmtime(p)))
    if not candidates:
        return None
    preferred_order = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'svg']
    candidates.sort(key=lambda x: (
        preferred_order.index(x[0].split('.')[-1]) if x[0].split('.')[-1] in preferred_order else 999,
        -x[1]
    ))
    return f"/static/img/{candidates[0][0]}"

def _validate_upload_file(file):
    if not file or file.filename == '':
        return "文件名为空"
    if not allowed_file(file.filename):
        return f"不支持的文件格式，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
    if request.content_length and request.content_length > MAX_UPLOAD_BYTES:
        return f"文件过大，最大允许 {MAX_UPLOAD_BYTES // (1024 * 1024)}MB"
    return None

def init_routes(app):
    @login_manager.user_loader
    def load_user(uid):
        return User.query.get(int(uid))

    @app.before_request
    def _auth_session_guard():
        try:
            if request.endpoint == 'static':
                return None
            msg = auth_security.check_session_fingerprint(request)
            if msg:
                flash(msg)
                return redirect(url_for('login'))
        except Exception:
            return None
        return None

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('console'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        next_url = (request.args.get('next') or '').strip()
        if request.method == 'GET':
            if (request.args.get('clear') or '').strip() in ('1', 'true', 'yes', 'on'):
                try:
                    logout_user()
                except Exception:
                    pass
                try:
                    session.clear()
                except Exception:
                    pass
            response = make_response(render_template('login_audio_final.html', next=next_url))
            if (request.args.get('clear') or '').strip() in ('1', 'true', 'yes', 'on'):
                cookie_name = current_app.config.get('SESSION_COOKIE_NAME', 'session')
                response.delete_cookie(cookie_name)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response

        data = request.form or {}
        username = data.get('username', '')
        password = data.get('password', '')
        ip = auth_security._get_client_ip(request)
        next_from_form = (data.get('next') or '').strip()
        if next_from_form:
            next_url = next_from_form

        allowed, deny_msg, _retry_after = auth_security.check_bruteforce_allowed(ip, username)
        if not allowed:
            msg = deny_msg or '登录请求被拦截'
            if _retry_after:
                msg = f"{msg}（约 {_retry_after} 秒后可重试）"
            flash(msg)
            if next_url:
                return redirect(url_for('login', next=next_url))
            return redirect(url_for('login'))

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            try:
                auth_security.record_login_attempt(ip, username, success=True)
            except Exception:
                pass
            login_user(user)
            try:
                auth_security.bind_session_fingerprint(request)
            except Exception:
                pass
            if next_url:
                parsed = urlparse(next_url)
                if parsed.scheme == '' and parsed.netloc == '' and next_url.startswith('/'):
                    return redirect(next_url)
            return redirect(url_for('console'))
        try:
            auth_security.record_login_attempt(ip, username, success=False)
        except Exception:
            pass
        flash('登录失败，用户名或密码错误')
        if next_url:
            return redirect(url_for('login', next=next_url))
        return redirect(url_for('login'))

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    @app.route('/console')
    @login_required
    def console():
        # 登录后的交互界面，提供跳转到仪表盘、测试页及 API
        response = make_response(render_template('console.html', user=current_user))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # 图片上传相关路由
    @app.route('/upload_mascot', methods=['GET'])
    @login_required
    def upload_mascot_page():
        return render_template('upload_mascot.html')

    @app.route('/upload_mascot', methods=['POST'])
    @login_required
    def upload_mascot():
        if 'mascot' not in request.files:
            return jsonify({"error": "没有选择文件"}), 400
        
        file = request.files['mascot']
        err = _validate_upload_file(file)
        if err:
            return jsonify({"error": err}), 400
        
        # 保存为 mascot + 原扩展名
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"mascot.{ext}"
        
        # 保存到 static/img 目录
        upload_folder = os.path.join(app.root_path, 'static', 'img')
        os.makedirs(upload_folder, exist_ok=True)
        
        # 删除所有旧的 mascot 文件，避免多个文件并存导致覆盖失败
        for old_ext in ALLOWED_EXTENSIONS:
            old_file = os.path.join(upload_folder, f"mascot.{old_ext}")
            if os.path.exists(old_file):
                backup_name = f"mascot_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{old_ext}"
                backup_path = os.path.join(upload_folder, backup_name)
                try:
                    os.rename(old_file, backup_path)
                except Exception:
                    # 如果重命名失败则直接删除
                    try:
                        os.remove(old_file)
                    except Exception:
                        pass
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        return jsonify({
            "status": "ok",
            "message": f"上传成功！文件已保存为 {filename}",
            "url": f"/static/img/{filename}",
            "cache_buster": datetime.now().timestamp()
        })

    @app.route('/get_current_mascot')
    def get_current_mascot():
        # 查找当前使用的吉祥物图片
        img_folder = os.path.join(app.root_path, 'static', 'img')
        mascot_files = []
        if os.path.exists(img_folder):
            for ext in ALLOWED_EXTENSIONS:
                pattern = f"mascot.{ext}"
                filepath = os.path.join(img_folder, pattern)
                if os.path.exists(filepath):
                    mascot_files.append({
                        "filename": pattern,
                        "url": f"/static/img/{pattern}",
                        "size": os.path.getsize(filepath),
                        "mtime": os.path.getmtime(filepath)
                    })
        # 选择最新或按常见扩展排序
        preferred_order = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'svg']
        mascot_files.sort(key=lambda x: (
            preferred_order.index(x['filename'].split('.')[-1]) if x['filename'].split('.')[-1] in preferred_order else 999,
            -x['mtime']
        ))
        mascot_url = mascot_files[0]['url'] if mascot_files else None
        return jsonify({"mascots": mascot_files, "mascot_url": mascot_url})

    # 测试页背景上传相关路由
    @app.route('/upload_test_bg', methods=['GET'])
    @login_required
    def upload_test_bg_page():
        return render_template('upload_test_bg.html')

    @app.route('/upload_test_bg', methods=['POST'])
    @login_required
    def upload_test_bg():
        if 'test_bg' not in request.files:
            return jsonify({"error": "没有选择文件"}), 400
        
        file = request.files['test_bg']
        err = _validate_upload_file(file)
        if err:
            return jsonify({"error": err}), 400
        
        # 保存为 test_bg + 原扩展名
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"test_bg.{ext}"
        
        # 保存到 static/img 目录
        upload_folder = os.path.join(app.root_path, 'static', 'img')
        os.makedirs(upload_folder, exist_ok=True)
        
        # 删除所有旧的 test_bg 文件（避免重叠）
        for old_ext in ALLOWED_EXTENSIONS:
            old_file = os.path.join(upload_folder, f"test_bg.{old_ext}")
            if os.path.exists(old_file):
                # 备份旧文件
                backup_name = f"test_bg_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{old_ext}"
                backup_path = os.path.join(upload_folder, backup_name)
                try:
                    os.rename(old_file, backup_path)
                except:
                    os.remove(old_file)
        
        # 保存新文件
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        return jsonify({
            "status": "ok",
            "message": f"测试页背景上传成功！文件已保存为 {filename}",
            "url": f"/static/img/{filename}",
            "cache_buster": datetime.now().timestamp()
        })

    @app.route('/get_current_test_bg')
    def get_current_test_bg():
        """获取当前测试页背景图"""
        url = _find_static_img_by_prefix(app, 'test_bg')
        return jsonify({"test_bg_url": url})

    @app.route('/test_xss', methods=['GET'])
    def test_xss_page():
        # 保持公开可访问的测试页面
        test_bg_url = _find_static_img_by_prefix(app, 'test_bg')
        return render_template('test_xss.html', test_bg_url=test_bg_url)

    @app.route('/test_xss', methods=['POST'])
    def test_xss_api():
        data = request.get_json() or {}
        payload = data.get('input', '')
        return jsonify({"message": f"已接收: {payload}"})

    @app.route('/xss/reflected')
    def xss_reflected():
        """反射型 XSS：URL 参数直接回显到页面"""
        search_query = request.args.get('q', '')
        return render_template('xss_reflected.html', query=search_query)

    @app.route('/xss/stored', methods=['GET', 'POST'])
    def xss_stored():
        """存储型 XSS：评论保存到数据库后展示"""
        if request.method == 'POST':
            data = request.get_json() or {}
            content = data.get('content', '')
            author = data.get('author', '匿名')
            if content:
                comment = Comment(content=content, author=author)
                db.session.add(comment)
                db.session.commit()
                return jsonify({"status": "ok", "message": "评论已发布"})
            return jsonify({"status": "error", "message": "评论内容不能为空"}), 400
        
        comments = Comment.query.order_by(Comment.timestamp.desc()).limit(20).all()
        return jsonify({
            "comments": [{
                "id": c.id,
                "content": c.content,
                "author": c.author,
                "timestamp": c.timestamp.isoformat()
            } for c in comments]
        })

    @app.route('/xss/stored/clear', methods=['POST'])
    def xss_stored_clear():
        """清空所有存储型 XSS 评论"""
        Comment.query.delete()
        db.session.commit()
        return jsonify({"status": "ok", "message": "已清空所有评论"})

    @app.route('/xss/stored/sandbox')
    def xss_stored_sandbox():
        """存储型 XSS 靶场展示页面（隔离环境）"""
        return render_template('xss_stored_sandbox.html')

    @app.route('/dashboard')
    @login_required
    def dashboard():
        mascot_url = _find_static_img_by_prefix(app, 'mascot')
        dashboard_bg_url = _find_static_img_by_prefix(app, 'dashboard_bg')
        return render_template(
            'dashboard.html',
            mascot_url=mascot_url,
            dashboard_bg_url=dashboard_bg_url,
            cache_buster=datetime.now().timestamp(),
        )

    @app.route('/upload_dashboard_bg', methods=['POST'])
    @login_required
    def upload_dashboard_bg():
        if 'dashboard_bg' not in request.files:
            return jsonify({"error": "没有选择文件"}), 400
        file = request.files['dashboard_bg']
        err = _validate_upload_file(file)
        if err:
            return jsonify({"error": err}), 400

        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"dashboard_bg.{ext}"

        upload_folder = os.path.join(app.root_path, 'static', 'img')
        os.makedirs(upload_folder, exist_ok=True)

        for old_ext in ALLOWED_EXTENSIONS:
            old_file = os.path.join(upload_folder, f"dashboard_bg.{old_ext}")
            if os.path.exists(old_file):
                backup_name = f"dashboard_bg_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.{old_ext}"
                backup_path = os.path.join(upload_folder, backup_name)
                try:
                    os.rename(old_file, backup_path)
                except Exception:
                    try:
                        os.remove(old_file)
                    except Exception:
                        pass

        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return jsonify({
            "status": "ok",
            "message": f"仪表盘背景上传成功！文件已保存为 {filename}",
            "url": f"/static/img/{filename}",
            "cache_buster": datetime.now().timestamp()
        })

    @app.route('/get_current_dashboard_bg')
    @login_required
    def get_current_dashboard_bg():
        url = _find_static_img_by_prefix(app, 'dashboard_bg')
        return jsonify({"dashboard_bg_url": url})

    @app.route('/api/stats/attacks')
    def api_attack_trend():
        end = datetime.utcnow().date()
        start = end - timedelta(days=13)
        days = [(start + timedelta(days=i)) for i in range(14)]
        counts = {d.isoformat(): 0 for d in days}
        rows = db.session.query(
            db.func.date(AttackLog.timestamp).label('d'),
            db.func.count(AttackLog.id)
        ).filter(AttackLog.timestamp >= start).group_by('d').all()
        for d, c in rows:
            counts[str(d)] = c
        return jsonify({"labels": list(counts.keys()), "data": list(counts.values())})

    @app.route('/api/stats/types')
    def api_attack_types():
        rows = db.session.query(AttackLog.payload).all()
        types = {"script":0, "alert":0, "javascript":0, "others":0}
        import re
        for (p,) in rows:
            if not p: 
                continue
            pl = p.lower()
            if re.search(r'<script', pl):
                types["script"] += 1
            elif 'alert' in pl:
                types["alert"] += 1
            elif 'javascript:' in pl:
                types["javascript"] += 1
            else:
                types["others"] += 1
        return jsonify({"labels": list(types.keys()), "data": list(types.values())})

    @app.route('/api/stats/top_ips')
    @login_required
    def api_top_ips():
        rows = db.session.query(
            AttackLog.ip,
            db.func.count(AttackLog.id).label('cnt')
        ).group_by(AttackLog.ip).order_by(db.desc('cnt')).limit(10).all()
        return jsonify({"labels": [r[0] for r in rows], "data": [int(r[1]) for r in rows]})

    @app.route('/api/stats/summary')
    @login_required
    def api_summary():
        total = db.session.query(db.func.count(AttackLog.id)).scalar() or 0
        blocked = db.session.query(db.func.count(AttackLog.id)).filter(AttackLog.blocked == True).scalar() or 0
        banned = db.session.query(db.func.count(BannedIP.id)).scalar() or 0
        return jsonify({
            "total_attacks": int(total),
            "blocked_attacks": int(blocked),
            "banned_ips": int(banned),
        })

    @app.route('/logs')
    @login_required
    def get_logs():
        logs = AttackLog.query.order_by(AttackLog.timestamp.desc()).limit(50).all()
        return jsonify([{'ip':l.ip,'payload':l.payload,'time':l.timestamp.isoformat(),'blocked':l.blocked} for l in logs])

    @app.route('/toggle_defense', methods=['POST'])
    @login_required
    def toggle_defense():
        data = request.get_json() or {}
        enable = bool(data.get('enabled', True))
        with app.app_context():
            s = Setting.query.filter_by(key='xss_defense_enabled').first()
            if not s:
                s = Setting(key='xss_defense_enabled', value='1' if enable else '0')
                db.session.add(s)
            else:
                s.value = '1' if enable else '0'
            db.session.commit()
        return jsonify({"enabled": enable})

    @app.route('/api/stats/ip_distribution')
    @login_required
    def api_ip_distribution():
        # 返回 top 20 IP 源及次数
        rows = db.session.query(
            AttackLog.ip,
            db.func.count(AttackLog.id).label('cnt')
        ).group_by(AttackLog.ip).order_by(db.desc('cnt')).limit(20).all()
        return jsonify({"labels":[r[0] for r in rows], "data":[r[1] for r in rows]})

    @app.route('/ban_ip', methods=['POST'])
    @login_required
    def ban_ip_api():
        data = request.get_json() or {}
        ip = data.get('ip')
        duration_minutes = data.get('duration')  # 可选：分钟
        permanent = bool(data.get('permanent', False))
        if not ip:
            return jsonify({"error":"missing ip"}), 400
        try:
            ipaddress.ip_address(ip)
        except Exception as e:
            return jsonify({"error":"invalid ip"}), 400
        with app.app_context():
            existing = BannedIP.query.filter_by(ip=ip).first()
            expires_at = None
            if duration_minutes:
                try:
                    expires_at = datetime.utcnow() + timedelta(minutes=int(duration_minutes))
                except Exception:
                    expires_at = None
            if existing:
                existing.permanent = permanent
                existing.expires_at = expires_at
            else:
                ban = BannedIP(ip=ip, permanent=permanent, expires_at=expires_at)
                db.session.add(ban)
            db.session.commit()
        return jsonify({"status":"ok"})

    @app.route('/unban_ip', methods=['POST'])
    @login_required
    def unban_ip_api():
        data = request.get_json() or {}
        ip = data.get('ip')
        if not ip:
            return jsonify({"error":"missing ip"}), 400
        with app.app_context():
            b = BannedIP.query.filter_by(ip=ip).first()
            if b:
                db.session.delete(b); db.session.commit()
        return jsonify({"status":"ok"})

    @app.route('/get_banned_ips')
    @login_required
    def get_banned_ips():
        rows = BannedIP.query.order_by(BannedIP.banned_at.desc()).all()
        def serialize(r):
            return {"ip": r.ip, "permanent": r.permanent, "banned_at": r.banned_at.isoformat(), "expires_at": (r.expires_at.isoformat() if r.expires_at else None)}
        return jsonify([serialize(r) for r in rows])

    @app.route('/attack/auth_security')
    def attack_auth_security_page():
        return render_template('attack_auth_security.html')

    @app.route('/api/auth_security/status')
    def api_auth_security_status():
        return jsonify(auth_security.get_status())

    @app.route('/api/auth_security/events')
    def api_auth_security_events():
        limit = request.args.get('limit')
        try:
            n = int(limit) if limit else 50
        except Exception:
            n = 50
        return jsonify({"events": auth_security.get_recent_events(limit=n)})

    @app.route('/api/auth_security/toggle', methods=['POST'])
    def api_auth_security_toggle():
        data = request.get_json() or {}
        flag = (data.get('flag') or '').strip()
        enabled = bool(data.get('enabled', True))
        auth_security.set_feature_flag(flag, enabled)
        return jsonify({"ok": True})

    @app.route('/api/auth/password_check', methods=['POST'])
    def api_password_check():
        data = request.get_json() or {}
        pwd = data.get('password') or ''
        ok, reasons = auth_security.validate_password_strength(pwd)
        return jsonify({"ok": bool(ok), "reasons": reasons})

    @app.route('/api/auth/change_password', methods=['POST'])
    @login_required
    def api_change_password():
        data = request.get_json() or {}
        new_pwd = data.get('new_password') or ''
        ip = auth_security._get_client_ip(request)
        ok, msg = auth_security.require_strong_password_or_raise(ip, new_pwd, context='change_password')
        if not ok:
            return jsonify({"ok": False, "error": msg or 'weak_password'}), 400
        try:
            current_user.set_password(new_pwd)
            db.session.commit()
        except Exception:
            db.session.rollback()
            return jsonify({"ok": False, "error": 'update_failed'}), 500
        return jsonify({"ok": True})

    # 攻击测试中心路由
    detector_manager = AttackDetectorManager(app, db)
    
    def simulate_command_injection(target):
        """模拟命令注入执行结果（仅用于演示）"""
        import re
        
        # 提取注入的命令
        commands = {
            'whoami': 'www-data',
            'id': 'uid=33(www-data) gid=33(www-data) groups=33(www-data)',
            'uname -a': 'Linux webserver 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux',
            'pwd': '/var/www/html',
            'hostname': 'webserver.local',
            'cat /etc/passwd': '''root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
mysql:x:111:116:MySQL Server,,,:/nonexistent:/bin/false
admin:x:1000:1000:Admin User:/home/admin:/bin/bash
alice:x:1001:1001:Alice:/home/alice:/bin/bash''',
            'ls -la': '''total 48
drwxr-xr-x  5 www-data www-data 4096 Dec 15 09:00 .
drwxr-xr-x  3 root     root     4096 Nov 20 10:30 ..
-rw-r--r--  1 www-data www-data  220 Nov 20 10:30 .bash_logout
-rw-r--r--  1 www-data www-data 3526 Nov 20 10:30 .bashrc
drwxr-xr-x  3 www-data www-data 4096 Dec 15 09:00 app
-rw-r--r--  1 www-data www-data  807 Nov 20 10:30 .profile
-rw-r--r--  1 www-data www-data 1024 Dec 15 09:00 config.php
-rw-r--r--  1 www-data www-data 2048 Dec 15 09:00 database.db
-rw-r--r--  1 www-data www-data  512 Dec 15 09:00 .env''',
            'ls': '''app
config.php
database.db
index.php
static
templates''',
            'env': '''PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOME=/var/www
USER=www-data
SHELL=/bin/bash
DATABASE_URL=sqlite:///database.db
SECRET_KEY=super_secret_key_12345
API_KEY=sk-1234567890abcdef''',
            'ps aux': '''USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1  18508  3256 ?        Ss   09:00   0:00 /sbin/init
www-data   123  0.5  2.1 245678 43210 ?        S    09:01   0:15 python3 app.py
www-data   456  0.1  0.8  98765 16543 ?        S    09:01   0:03 nginx worker
mysql      789  0.3  5.2 876543 98765 ?        Ssl  09:00   0:08 /usr/sbin/mysqld''',
            'netstat -an': '''Active Internet connections (servers and established)
Proto Recv-Q Send-Q Local Address           Foreign Address         State
tcp        0      0 0.0.0.0:80              0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:443             0.0.0.0:*               LISTEN
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN''',
            'ifconfig': '''eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255
        ether 00:0c:29:3a:2b:1c  txqueuelen 1000  (Ethernet)''',
            'ip addr': '''2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:0c:29:3a:2b:1c brd ff:ff:ff:ff:ff:ff
    inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::20c:29ff:fe3a:2b1c/64 scope link
       valid_lft forever preferred_lft forever''',
            'ipconfig': '''Windows IP Configuration

Ethernet adapter Ethernet:

   Connection-specific DNS Suffix  . : local
   IPv4 Address. . . . . . . . . . . : 192.168.1.100
   Subnet Mask . . . . . . . . . . . : 255.255.255.0
   Default Gateway . . . . . . . . . : 192.168.1.1''',
        }
        
        # 检测常见命令模式
        target_lower = target.lower()
        
        # 构建完整输出
        output_parts = []
        
        # 先显示ping输出
        clean_target = re.split(r'[;&|`$&]', target)[0].strip()
        output_parts.append(f'PING {clean_target} (127.0.0.1): 56 data bytes')
        output_parts.append('64 bytes from 127.0.0.1: icmp_seq=0 ttl=64 time=0.123 ms')
        output_parts.append(f'\n--- {clean_target} ping statistics ---')
        output_parts.append('2 packets transmitted, 2 packets received, 0.0% packet loss\n')
        
        # 检测并添加注入命令的输出
        for cmd, result in commands.items():
            if cmd in target_lower:
                output_parts.append(f'\n[命令注入执行: {cmd}]')
                output_parts.append(result)
                break
        else:
            # 通用命令检测
            if 'cat' in target_lower and 'passwd' in target_lower:
                output_parts.append('\n[命令注入执行: cat /etc/passwd]')
                output_parts.append(commands['cat /etc/passwd'])
            elif 'whoami' in target_lower:
                output_parts.append('\n[命令注入执行: whoami]')
                output_parts.append(commands['whoami'])
            elif 'uname' in target_lower:
                output_parts.append('\n[命令注入执行: uname -a]')
                output_parts.append(commands['uname -a'])
            elif re.search(r'\bls\b', target_lower):
                if '-la' in target_lower or '-al' in target_lower:
                    output_parts.append('\n[命令注入执行: ls -la]')
                    output_parts.append(commands['ls -la'])
                else:
                    output_parts.append('\n[命令注入执行: ls]')
                    output_parts.append(commands['ls'])
            elif 'env' in target_lower:
                output_parts.append('\n[命令注入执行: env]')
                output_parts.append(commands['env'])
            elif 'ps' in target_lower:
                output_parts.append('\n[命令注入执行: ps aux]')
                output_parts.append(commands['ps aux'])
            elif 'netstat' in target_lower:
                output_parts.append('\n[命令注入执行: netstat -an]')
                output_parts.append(commands['netstat -an'])
            elif 'ipconfig' in target_lower:
                output_parts.append('\n[命令注入执行: ipconfig]')
                output_parts.append(commands['ipconfig'])
            elif 'ifconfig' in target_lower or 'ip addr' in target_lower:
                if 'ip addr' in target_lower:
                    output_parts.append('\n[命令注入执行: ip addr]')
                    output_parts.append(commands['ip addr'])
                else:
                    output_parts.append('\n[命令注入执行: ifconfig]')
                    output_parts.append(commands['ifconfig'])
            elif 'pwd' in target_lower:
                output_parts.append('\n[命令注入执行: pwd]')
                output_parts.append(commands['pwd'])
            elif 'hostname' in target_lower:
                output_parts.append('\n[命令注入执行: hostname]')
                output_parts.append(commands['hostname'])
            elif 'id' in target_lower and not 'void' in target_lower:
                output_parts.append('\n[命令注入执行: id]')
                output_parts.append(commands['id'])
            else:
                # 默认显示一个通用的命令执行结果
                output_parts.append('\n[检测到命令注入，但命令执行失败或无输出]')
        
        return '\n'.join(output_parts)
    
    def log_attack(ip, payload, attack_info, blocked=True, target_url='', user_agent=''):
        """记录攻击日志"""
        attack = attack_info['attacks'][0] if attack_info.get('attacks') else {}
        log = AttackLog(
            ip=ip,
            payload=payload[:2000],
            blocked=blocked,
            attack_type=attack.get('type', 'unknown'),
            attack_category=attack.get('category', 'unknown'),
            severity=attack.get('severity', 'medium'),
            target_url=target_url[:500],
            user_agent=user_agent[:500]
        )
        db.session.add(log)
        db.session.commit()

    @app.route('/attack_hub')
    def attack_hub():
        return render_template('attack_hub.html')

    @app.route('/api/attack/stats')
    def attack_stats():
        """攻击统计API"""
        total = AttackLog.query.count()
        blocked = AttackLog.query.filter_by(blocked=True).count()
        types = db.session.query(AttackLog.attack_type).distinct().count()
        return jsonify({
            'total': total,
            'blocked': blocked,
            'types': types
        })

    @app.route('/api/attack/type_breakdown')
    def api_attack_type_breakdown():
        rows = db.session.query(
            AttackLog.attack_type,
            db.func.count(AttackLog.id).label('cnt')
        ).group_by(AttackLog.attack_type).order_by(db.desc('cnt')).all()
        labels = []
        data = []
        for t, c in rows:
            labels.append(t or 'unknown')
            data.append(int(c))
        return jsonify({"labels": labels, "data": data})

    @app.route('/api/attack/logs')
    def api_attack_logs():
        limit = request.args.get('limit')
        offset = request.args.get('offset')
        attack_type = (request.args.get('type') or '').strip()
        severity = (request.args.get('severity') or '').strip()
        blocked = (request.args.get('blocked') or '').strip().lower()
        ip = (request.args.get('ip') or '').strip()
        search = (request.args.get('q') or '').strip()

        try:
            n = int(limit) if limit else 50
        except Exception:
            n = 50
        try:
            o = int(offset) if offset else 0
        except Exception:
            o = 0

        n = max(1, min(n, 200))
        o = max(0, o)

        qset = AttackLog.query
        if attack_type:
            qset = qset.filter(AttackLog.attack_type == attack_type)
        if severity:
            qset = qset.filter(AttackLog.severity == severity)
        if blocked in ('true', 'false'):
            qset = qset.filter(AttackLog.blocked == (blocked == 'true'))
        if ip:
            qset = qset.filter(AttackLog.ip == ip)
        if search:
            qset = qset.filter(AttackLog.payload.ilike(f"%{search}%"))

        rows = qset.order_by(AttackLog.timestamp.desc()).offset(o).limit(n).all()
        return jsonify({
            "logs": [
                {
                    "id": int(l.id),
                    "ip": l.ip,
                    "payload": l.payload,
                    "time": l.timestamp.isoformat(),
                    "blocked": bool(l.blocked),
                    "attack_type": l.attack_type,
                    "attack_category": l.attack_category,
                    "severity": l.severity,
                    "target_url": l.target_url,
                    "user_agent": l.user_agent,
                }
                for l in rows
            ]
        })

    @app.route('/api/dashboard/stats', methods=['GET'])
    @login_required
    def dashboard_stats_api():
        """为 3D 仪表盘提供实时统计数据"""
        total_attacks = AttackLog.query.count()
        blocked_count = AttackLog.query.filter_by(blocked=True).count()

        success_rate = 0
        if total_attacks > 0:
            success_rate = round((blocked_count / total_attacks) * 100, 1)

        type_counts = {
            'sqli': AttackLog.query.filter(AttackLog.attack_type.ilike('%sql%')).count(),
            'xss': AttackLog.query.filter(AttackLog.attack_type.ilike('%xss%')).count(),
            'cmdi': AttackLog.query.filter(AttackLog.attack_type.ilike('%cmd%')).count(),
            'path': AttackLog.query.filter(AttackLog.attack_type.ilike('%path%')).count(),
        }

        return jsonify({
            'total_attacks': total_attacks,
            'blocked_attacks': blocked_count,
            'success_rate': success_rate,
            'attack_types_count': 4,
            'details': type_counts
        })

    @app.route('/test_sqli')
    def test_sqli():
        """SQL注入测试页面"""
        if VulnerableUser.query.count() == 0:
            sample_users = [
                VulnerableUser(username='admin', email='admin@example.com', password='admin123', role='admin'),
                VulnerableUser(username='alice', email='alice@example.com', password='alice2024', role='user'),
                VulnerableUser(username='bob', email='bob@example.com', password='bob@secure', role='user'),
                VulnerableUser(username='charlie', email='charlie@example.com', password='charlie99', role='user'),
                VulnerableUser(username='david', email='david@example.com', password='david_pwd', role='user'),
            ]
            for user in sample_users:
                db.session.add(user)
            db.session.commit()
        return render_template('test_sqli.html')

    @app.route('/attack/sqli/search', methods=['POST'])
    def sqli_search():
        """SQL注入搜索测试"""
        try:
            data = request.get_json() or {}
            query = data.get('query', '')
            defense_enabled = data.get('defense_enabled', True)
            simulated_ip = data.get('simulated_ip', '')

            ip = simulated_ip if simulated_ip else request.remote_addr

            if defense_enabled:
                detection = detector_manager.detect_all(query)

                if detection['detected']:
                    attack_info = detection['attacks'][0]
                    log_attack(ip, query, detection, blocked=True, target_url=request.path, user_agent=request.headers.get('User-Agent', ''))
                    return jsonify({
                        'blocked': True,
                        'attack_type': attack_info['type'],
                        'description': attack_info['description'],
                        'severity': attack_info['severity'],
                        'category': attack_info['category']
                    })
            else:
                detection = detector_manager.detect_all(query)
                if detection['detected']:
                    attack_info = detection['attacks'][0]
                    log_attack(ip, query, detection, blocked=False, target_url=request.path, user_agent=request.headers.get('User-Agent', ''))
                    users = VulnerableUser.query.all()
                    return jsonify({
                        'blocked': False,
                        'defense_enabled': defense_enabled,
                        'simulated_ip': ip,
                        'attack_detected': True,
                        'attack_type': attack_info['type'],
                        'users': [{
                            'id': u.id,
                            'username': u.username,
                            'email': u.email,
                            'role': u.role,
                            'password': u.password
                        } for u in users]
                    })

            users = VulnerableUser.query.filter(
                VulnerableUser.username.like(f'%{query}%')
            ).all()

            return jsonify({
                'blocked': False,
                'defense_enabled': defense_enabled,
                'simulated_ip': ip,
                'users': [{
                    'id': u.id,
                    'username': u.username,
                    'email': u.email,
                    'role': u.role
                } for u in users]
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    
    @app.route('/attack/sqli/sandbox')
    def sqli_sandbox():
        """SQL注入靶场沙箱"""
        return render_template('sqli_sandbox.html')
    
    @app.route('/attack/sqli/database')
    def sqli_database():
        """获取完整数据库（靶场）"""
        users = VulnerableUser.query.all()
        return jsonify({
            'users': [{
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'password': u.password,
                'role': u.role,
                'created_at': u.created_at.isoformat()
            } for u in users]
        })
    
    @app.route('/attack/sqli/reset', methods=['POST'])
    def sqli_reset():
        """重置SQL注入靶场数据"""
        VulnerableUser.query.delete()
        
        # 创建示例数据
        sample_users = [
            VulnerableUser(username='admin', email='admin@example.com', password='admin123', role='admin'),
            VulnerableUser(username='alice', email='alice@example.com', password='alice2024', role='user'),
            VulnerableUser(username='bob', email='bob@example.com', password='bob@secure', role='user'),
            VulnerableUser(username='charlie', email='charlie@example.com', password='charlie99', role='user'),
            VulnerableUser(username='david', email='david@example.com', password='david_pwd', role='user'),
        ]
        
        for user in sample_users:
            db.session.add(user)
        
        db.session.commit()
        return jsonify({'status': 'ok', 'message': '靶场数据已重置'})
    
    # 命令注入测试路由
    @app.route('/test_cmdi')
    def test_cmdi():
        """命令注入测试页面"""
        return render_template('test_cmdi.html')
    
    @app.route('/attack/cmdi/ping', methods=['POST'])
    def cmdi_ping():
        """命令注入Ping测试"""
        try:
            data = request.get_json() or {}
            target = data.get('target', '')
            defense_enabled = data.get('defense_enabled', True)
            simulated_ip = data.get('simulated_ip', '')
            
            ip = simulated_ip if simulated_ip else request.remote_addr
            
            if defense_enabled:
                detection = detector_manager.detect_all(target)
                
                if detection['detected']:
                    attack_info = detection['attacks'][0]
                    log_attack(ip, target, detection, blocked=True, target_url=request.path, user_agent=request.headers.get('User-Agent', ''))
                    return jsonify({
                        'blocked': True,
                        'attack_type': attack_info['type'],
                        'description': attack_info['description'],
                        'severity': attack_info['severity'],
                        'category': attack_info['category']
                    })
            else:
                import re
                detection = detector_manager.detect_all(target)

                looks_injected = bool(re.search(r'(;|\||&&|\|\||`|\$\(\))', target))

                if detection['detected'] or looks_injected:
                    if detection['detected']:
                        attack_info = detection['attacks'][0]
                        info_for_log = detection
                    else:
                        attack_info = {
                            'type': 'cmdi',
                            'category': 'injection',
                            'severity': 'critical',
                            'description': '疑似命令注入（基于分隔符触发演示）'
                        }
                        info_for_log = {'detected': True, 'attacks': [attack_info]}

                    log_attack(ip, target, info_for_log, blocked=False, target_url=request.path, user_agent=request.headers.get('User-Agent', ''))

                    injected_output = simulate_command_injection(target)
                    return jsonify({
                        'blocked': False,
                        'defense_enabled': defense_enabled,
                        'simulated_ip': ip,
                        'attack_detected': True,
                        'attack_type': attack_info['type'],
                        'output': injected_output
                    })
            
            # 正常ping输出
            return jsonify({
                'blocked': False,
                'defense_enabled': defense_enabled,
                'simulated_ip': ip,
                'output': f'PING {target} (127.0.0.1): 56 data bytes\n64 bytes from 127.0.0.1: icmp_seq=0 ttl=64 time=0.123 ms\n64 bytes from 127.0.0.1: icmp_seq=1 ttl=64 time=0.089 ms\n\n--- {target} ping statistics ---\n2 packets transmitted, 2 packets received, 0.0% packet loss'
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500
    
    # 目录遍历测试路由
    @app.route('/test_path_traversal')
    def test_path_traversal():
        """目录遍历测试页面"""
        return render_template('test_path_traversal.html')
    
    @app.route('/attack/path/view', methods=['POST'])
    def path_view():
        """目录遍历文件查看测试"""
        try:
            data = request.get_json() or {}
            filepath = data.get('filepath', '')
            defense_enabled = data.get('defense_enabled', True)
            simulated_ip = data.get('simulated_ip', '')
            
            ip = simulated_ip if simulated_ip else request.remote_addr
            
            if defense_enabled:
                detection = detector_manager.detect_all(filepath)
                
                if detection['detected']:
                    attack_info = detection['attacks'][0]
                    log_attack(ip, filepath, detection, blocked=True, target_url=request.path, user_agent=request.headers.get('User-Agent', ''))
                    return jsonify({
                        'blocked': True,
                        'attack_type': attack_info['type'],
                        'description': attack_info['description'],
                        'severity': attack_info['severity'],
                        'category': attack_info['category']
                    })
            else:
                detection = detector_manager.detect_all(filepath)
                if detection['detected']:
                    attack_info = detection['attacks'][0]
                    log_attack(ip, filepath, detection, blocked=False, target_url=request.path, user_agent=request.headers.get('User-Agent', ''))
            
            allowed_files = {
                'documents/readme.txt': 'Welcome to our application!\n\nThis is a sample readme file.\n\nFeatures:\n- User management\n- File upload\n- Secure authentication',
                'documents/guide.pdf': '[PDF Content] User Guide - Version 1.0',
                'images/logo.png': '[PNG Image Data]',
                'public/index.html': '<!DOCTYPE html>\n<html>\n<head><title>Home</title></head>\n<body><h1>Welcome</h1></body>\n</html>'
            }
            
            if filepath in allowed_files:
                return jsonify({
                    'blocked': False,
                    'defense_enabled': defense_enabled,
                    'simulated_ip': ip,
                    'filename': filepath,
                    'content': allowed_files[filepath]
                })
            else:
                return jsonify({'error': '文件不存在或无权访问'}), 404
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'服务器错误: {str(e)}'}), 500