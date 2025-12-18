from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict

from flask import request, session
from flask_login import current_user, logout_user

from . import db
from .models import AttackLog, Setting, AuthLoginAttempt
from sqlalchemy import func


def _get_client_ip(req) -> str:
    xff = (req.headers.get('X-Forwarded-For') or '').split(',')[0].strip()
    if xff:
        ip = xff
    else:
        ip = (req.remote_addr or '127.0.0.1').strip()
    try:
        import ipaddress
        a = ipaddress.ip_address(ip)
        if a.version == 6 and a.is_loopback:
            return '127.0.0.1'
    except Exception:
        pass
    return ip


def _get_user_agent(req) -> str:
    return (req.headers.get('User-Agent') or '')[:500]


def _setting_bool(key: str, default: bool = True) -> bool:
    s = Setting.query.filter_by(key=key).first()
    if not s or s.value is None:
        return default
    return str(s.value).strip() in ('1', 'true', 'True', 'yes', 'on')


def _set_setting_bool(key: str, enabled: bool) -> None:
    s = Setting.query.filter_by(key=key).first()
    if not s:
        s = Setting(key=key, value='1' if enabled else '0')
        db.session.add(s)
    else:
        s.value = '1' if enabled else '0'
    db.session.commit()


def is_auth_security_enabled() -> bool:
    return _setting_bool('auth_security_enabled', True)


def is_bruteforce_enabled() -> bool:
    return _setting_bool('auth_bruteforce_enabled', True)


def is_weak_password_enabled() -> bool:
    return _setting_bool('auth_weak_password_enabled', True)


def is_session_guard_enabled() -> bool:
    return _setting_bool('auth_session_guard_enabled', True)


def set_feature_flag(flag: str, enabled: bool) -> None:
    mapping = {
        'auth_security_enabled': 'auth_security_enabled',
        'auth_bruteforce_enabled': 'auth_bruteforce_enabled',
        'auth_weak_password_enabled': 'auth_weak_password_enabled',
        'auth_session_guard_enabled': 'auth_session_guard_enabled',
    }
    key = mapping.get(flag)
    if not key:
        raise ValueError('unknown flag')
    _set_setting_bool(key, enabled)


@dataclass
class BruteForceConfig:
    username_fail_window_seconds: int = 120
    username_fail_threshold: int = 5

    ip_window_seconds: int = 180
    ip_distinct_usernames_threshold: int = 6

    block_cooldown_seconds: int = 300


BRUTE_FORCE_CFG = BruteForceConfig()


def record_login_attempt(ip: str, username: str, success: bool) -> None:
    a = AuthLoginAttempt(
        ip=ip,
        username=(username or '')[:80],
        success=bool(success),
        user_agent=_get_user_agent(request),
    )
    db.session.add(a)
    db.session.commit()


def _log_auth_attack(ip: str, attack_type: str, severity: str, message: str, blocked: bool = True) -> None:
    log = AttackLog(
        ip=ip,
        payload=(message or '')[:500],
        blocked=blocked,
        attack_type=attack_type,
        attack_category='behavioral',
        severity=severity,
        target_url=(request.path or '')[:500],
        user_agent=_get_user_agent(request),
    )
    db.session.add(log)
    db.session.commit()


def check_bruteforce_allowed(ip: str, username: str) -> Tuple[bool, Optional[str], int]:
    if not (is_auth_security_enabled() and is_bruteforce_enabled()):
        return True, None, 0

    now = datetime.utcnow()

    user_cutoff = now - timedelta(seconds=BRUTE_FORCE_CFG.username_fail_window_seconds)
    user_fail_count = AuthLoginAttempt.query.filter(
        AuthLoginAttempt.username == (username or '')[:80],
        AuthLoginAttempt.success == False,
        AuthLoginAttempt.timestamp >= user_cutoff,
    ).count()

    if user_fail_count >= BRUTE_FORCE_CFG.username_fail_threshold:
        retry_after = 0
        try:
            last_n = AuthLoginAttempt.query.filter(
                AuthLoginAttempt.username == (username or '')[:80],
                AuthLoginAttempt.success == False,
            ).order_by(AuthLoginAttempt.timestamp.desc()).limit(BRUTE_FORCE_CFG.username_fail_threshold).all()
            if last_n:
                oldest = last_n[-1].timestamp
                ready_at = oldest + timedelta(seconds=BRUTE_FORCE_CFG.username_fail_window_seconds)
                retry_after = max(0, int((ready_at - now).total_seconds()))
        except Exception:
            retry_after = 0
        _log_auth_attack(ip, 'brute_force', 'high', f'Blocked: username brute force username={username} fails={user_fail_count}')
        return False, '同一账号短时间内失败次数过多，请稍后再试', retry_after

    ip_cutoff = now - timedelta(seconds=BRUTE_FORCE_CFG.ip_window_seconds)
    rows = db.session.query(AuthLoginAttempt.username).filter(
        AuthLoginAttempt.ip == ip,
        AuthLoginAttempt.timestamp >= ip_cutoff,
    ).distinct().all()
    distinct_usernames = len(rows)

    if distinct_usernames >= BRUTE_FORCE_CFG.ip_distinct_usernames_threshold:
        retry_after = 0
        try:
            oldest_ts = db.session.query(func.min(AuthLoginAttempt.timestamp)).filter(
                AuthLoginAttempt.ip == ip,
                AuthLoginAttempt.timestamp >= ip_cutoff,
            ).scalar()
            if oldest_ts:
                ready_at = oldest_ts + timedelta(seconds=BRUTE_FORCE_CFG.ip_window_seconds)
                retry_after = max(0, int((ready_at - now).total_seconds()))
        except Exception:
            retry_after = 0
        _log_auth_attack(ip, 'brute_force', 'high', f'Blocked: credential stuffing ip={ip} distinct_usernames={distinct_usernames}')
        return False, '短时间内尝试多个账号，疑似撞库，请稍后再试', retry_after

    return True, None, 0


COMMON_WEAK_PASSWORDS = {
    'admin', 'password', '123456', '12345678', '111111', 'qwerty', 'abc123',
    'letmein', 'iloveyou', '000000', '123123', 'admin123', 'root', 'toor'
}


def validate_password_strength(pwd: str) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    if pwd is None:
        return False, ['密码不能为空']

    s = str(pwd)
    if len(s) < 8:
        reasons.append('密码长度至少 8 位')

    has_lower = any('a' <= c <= 'z' for c in s)
    has_upper = any('A' <= c <= 'Z' for c in s)
    has_digit = any(c.isdigit() for c in s)
    has_symbol = any(not c.isalnum() for c in s)

    if not (has_lower and has_upper):
        reasons.append('至少包含大小写字母')
    if not has_digit:
        reasons.append('至少包含数字')
    if not has_symbol:
        reasons.append('至少包含特殊字符')

    if s.lower() in COMMON_WEAK_PASSWORDS:
        reasons.append('密码过于常见，属于弱口令')

    return (len(reasons) == 0), reasons


def require_strong_password_or_raise(ip: str, pwd: str, context: str) -> Tuple[bool, Optional[str]]:
    if not (is_auth_security_enabled() and is_weak_password_enabled()):
        return True, None

    ok, reasons = validate_password_strength(pwd)
    if ok:
        return True, None

    msg = '；'.join(reasons)
    _log_auth_attack(ip, 'weak_password', 'medium', f'Weak password blocked context={context} reasons={msg}', blocked=True)
    return False, msg


SESSION_FP_KEY = '__auth_session_fp'
SESSION_FP_TS_KEY = '__auth_session_fp_ts'


def _ip_same_subnet(ip1: str, ip2: str) -> bool:
    try:
        import ipaddress
        a1 = ipaddress.ip_address(ip1)
        a2 = ipaddress.ip_address(ip2)
        if a1.is_loopback and a2.is_loopback:
            return True
        if a1.version != a2.version:
            return False
        if a1.version == 4:
            n1 = ipaddress.ip_network(f'{ip1}/24', strict=False)
            n2 = ipaddress.ip_network(f'{ip2}/24', strict=False)
            return n1.network_address == n2.network_address
        return ip1 == ip2
    except Exception:
        return ip1 == ip2


def bind_session_fingerprint(req) -> None:
    ip = _get_client_ip(req)
    ua = _get_user_agent(req)
    session[SESSION_FP_KEY] = {'ip': ip, 'ua': ua}
    session[SESSION_FP_TS_KEY] = int(datetime.utcnow().timestamp())


def check_session_fingerprint(req) -> Optional[str]:
    if not (is_auth_security_enabled() and is_session_guard_enabled()):
        return None

    if not current_user.is_authenticated:
        return None

    fp = session.get(SESSION_FP_KEY)
    if not isinstance(fp, dict) or 'ip' not in fp or 'ua' not in fp:
        bind_session_fingerprint(req)
        return None

    ip_now = _get_client_ip(req)
    ua_now = _get_user_agent(req)
    ip_then = str(fp.get('ip') or '')
    ua_then = str(fp.get('ua') or '')

    ua_changed = (ua_then != ua_now) and (ua_then != '')
    ip_changed = (ip_then != ip_now) and (ip_then != '') and (not _ip_same_subnet(ip_then, ip_now))

    if ua_changed or ip_changed:
        reason = f'session fingerprint changed ip:{ip_then}->{ip_now} ua_changed:{1 if ua_changed else 0}'
        try:
            _log_auth_attack(ip_now, 'session_hijack', 'high', f'Blocked: {reason}', blocked=True)
        except Exception:
            pass
        try:
            logout_user()
        except Exception:
            pass
        try:
            session.clear()
        except Exception:
            pass
        return '检测到会话异常（IP/UA 发生突变），已强制退出登录'

    return None


def get_status(ip: Optional[str] = None) -> Dict:
    ip = ip or _get_client_ip(request)
    now = datetime.utcnow()
    user_cutoff = now - timedelta(seconds=BRUTE_FORCE_CFG.username_fail_window_seconds)
    ip_cutoff = now - timedelta(seconds=BRUTE_FORCE_CFG.ip_window_seconds)

    recent_failed_total = AuthLoginAttempt.query.filter(
        AuthLoginAttempt.success == False,
        AuthLoginAttempt.timestamp >= user_cutoff,
    ).count()

    recent_ip_distinct_users = db.session.query(AuthLoginAttempt.username).filter(
        AuthLoginAttempt.ip == ip,
        AuthLoginAttempt.timestamp >= ip_cutoff,
    ).distinct().count()

    return {
        'enabled': is_auth_security_enabled(),
        'bruteforce_enabled': is_bruteforce_enabled(),
        'weak_password_enabled': is_weak_password_enabled(),
        'session_guard_enabled': is_session_guard_enabled(),
        'client_ip': ip,
        'bruteforce': {
            'username_fail_threshold': BRUTE_FORCE_CFG.username_fail_threshold,
            'username_fail_window_seconds': BRUTE_FORCE_CFG.username_fail_window_seconds,
            'ip_distinct_usernames_threshold': BRUTE_FORCE_CFG.ip_distinct_usernames_threshold,
            'ip_window_seconds': BRUTE_FORCE_CFG.ip_window_seconds,
            'recent_failed_total_in_window': int(recent_failed_total),
            'recent_distinct_usernames_for_ip': int(recent_ip_distinct_users),
        },
    }


def get_recent_events(limit: int = 50) -> List[Dict]:
    q = AttackLog.query.filter(AttackLog.attack_type.in_(['brute_force', 'weak_password', 'session_hijack']))
    rows = q.order_by(AttackLog.timestamp.desc()).limit(int(limit)).all()
    out: List[Dict] = []
    for r in rows:
        out.append({
            'timestamp': r.timestamp.isoformat() if r.timestamp else None,
            'type': r.attack_type,
            'severity': r.severity,
            'ip': r.ip,
            'blocked': bool(r.blocked),
            'target_url': r.target_url,
            'user_agent': r.user_agent,
            'payload': r.payload,
        })
    return out
