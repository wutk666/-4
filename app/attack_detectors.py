"""
多攻击类型检测器模块
支持 XSS, SQL注入, 命令注入, 目录遍历等多种攻击检测
"""
import re
from typing import Tuple, Optional, Dict
from datetime import datetime, timedelta

class AttackDetector:
    """攻击检测基类"""
    
    def __init__(self):
        self.attack_type = "unknown"
        self.attack_category = "unknown"
        self.severity = "medium"
    
    def detect(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        检测是否存在攻击
        返回: (是否检测到攻击, 匹配的模式描述)
        """
        raise NotImplementedError


class XSSDetector(AttackDetector):
    """XSS 攻击检测器"""
    
    def __init__(self):
        super().__init__()
        self.attack_type = "xss"
        self.attack_category = "injection"
        self.severity = "high"
        
        self.patterns = [
            (r'<script[^>]*>.*?</script>', 'Script标签注入'),
            (r'javascript\s*:', 'JavaScript伪协议'),
            (r'on\w+\s*=', '事件处理器注入'),
            (r'<iframe[^>]*>', 'iframe注入'),
            (r'<embed[^>]*>', 'embed标签注入'),
            (r'<object[^>]*>', 'object标签注入'),
            (r'eval\s*\(', 'eval函数调用'),
            (r'alert\s*\(', 'alert函数调用'),
            (r'document\.cookie', 'Cookie窃取尝试'),
            (r'document\.write', 'document.write注入'),
        ]
    
    def detect(self, content: str) -> Tuple[bool, Optional[str]]:
        if not content:
            return False, None
        
        for pattern, description in self.patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                return True, description
        
        return False, None


class SQLInjectionDetector(AttackDetector):
    """SQL 注入攻击检测器"""
    
    def __init__(self):
        super().__init__()
        self.attack_type = "sqli"
        self.attack_category = "injection"
        self.severity = "critical"
        
        self.patterns = [
            (r"'\s*OR\s+'?1'?\s*=\s*'?1", 'OR 1=1 注入'),
            (r"'\s*OR\s+'?1'?\s*=\s*'?1\s*--", 'OR 1=1 注释注入'),
            (r"'\s*OR\s+'?1'?\s*=\s*'?1\s*#", 'OR 1=1 井号注释'),
            (r"'\s*OR\s+'?1'?\s*=\s*'?1\s*/\*", 'OR 1=1 块注释'),
            (r"'\s*;\s*DROP\s+TABLE", 'DROP TABLE 注入'),
            (r"'\s*;\s*DELETE\s+FROM", 'DELETE 注入'),
            (r"'\s*;\s*UPDATE\s+", 'UPDATE 注入'),
            (r"'\s*UNION\s+SELECT", 'UNION SELECT 注入'),
            (r"'\s*AND\s+'?1'?\s*=\s*'?2", 'AND 1=2 注入'),
            (r"admin'\s*--", 'admin注释绕过'),
            (r"admin'\s*#", 'admin井号绕过'),
            (r"\bEXEC\s*\(", 'EXEC执行注入'),
            (r"\bEXECUTE\s+", 'EXECUTE注入'),
            (r"xp_cmdshell", 'xp_cmdshell注入'),
            (r"BENCHMARK\s*\(", 'BENCHMARK时间盲注'),
            (r"SLEEP\s*\(", 'SLEEP时间盲注'),
            (r"WAITFOR\s+DELAY", 'WAITFOR延迟注入'),
            (r"LOAD_FILE\s*\(", '文件读取注入'),
            (r"INTO\s+OUTFILE", '文件写入注入'),
            (r"'\s*\+\s*'", '字符串拼接注入'),
            (r"0x[0-9a-fA-F]+", '十六进制编码注入'),
            (r"CHAR\s*\(\d+", 'CHAR编码注入'),
        ]
    
    def detect(self, content: str) -> Tuple[bool, Optional[str]]:
        if not content:
            return False, None
        
        for pattern, description in self.patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True, description
        
        return False, None


class CommandInjectionDetector(AttackDetector):
    """命令注入攻击检测器"""
    
    def __init__(self):
        super().__init__()
        self.attack_type = "cmdi"
        self.attack_category = "injection"
        self.severity = "critical"
        
        self.patterns = [
            (r'(;|\||&&|\|\||`|\$\()', '命令拼接/分隔符注入'),
            (r';\s*cat\s+/etc/passwd', 'cat /etc/passwd 命令'),
            (r';\s*ls\s+-la', 'ls 目录列举'),
            (r';\s*ls\b', 'ls 目录列举'),
            (r';\s*whoami', 'whoami 用户探测'),
            (r';\s*id\b', 'id 命令执行'),
            (r';\s*uname\s+-a', 'uname 系统信息'),
            (r';\s*env\b', 'env 环境变量泄露'),
            (r';\s*ps\s+aux', 'ps aux 进程列表'),
            (r';\s*netstat\s+-an', 'netstat 网络连接'),
            (r';\s*ifconfig\b', 'ifconfig 网络配置'),
            (r';\s*ip\s+addr\b', 'ip addr 网络配置'),
            (r';\s*ipconfig\b', 'ipconfig 网络配置'),
            (r';\s*wget\s+', 'wget 文件下载'),
            (r';\s*curl\s+', 'curl 请求注入'),
            (r';\s*nc\s+', 'netcat 反弹shell'),
            (r';\s*bash\s+-i', 'bash 交互shell'),
            (r';\s*sh\s+-i', 'sh 交互shell'),
            (r';\s*python\s+-c', 'python 命令执行'),
            (r';\s*perl\s+-e', 'perl 命令执行'),
            (r';\s*ruby\s+-e', 'ruby 命令执行'),
            (r';\s*rm\s+-rf', 'rm 删除命令'),
            (r';\s*chmod\s+', 'chmod 权限修改'),
            (r';\s*chown\s+', 'chown 所有者修改'),
            (r'\|\s*cat\s+', '管道符 cat'),
            (r'\|\s*grep\s+', '管道符 grep'),
            (r'\|\s*id\b', '管道符 id'),
            (r'`.*`', '反引号命令执行'),
            (r'\$\(.*\)', '$() 命令替换'),
            (r'&&\s*\w+', '&& 命令链接'),
            (r'\|\|\s*\w+', '|| 命令链接'),
            (r'>\s*/dev/null', '输出重定向'),
            (r'<\s*/etc/', '输入重定向敏感文件'),
        ]
    
    def detect(self, content: str) -> Tuple[bool, Optional[str]]:
        if not content:
            return False, None
        
        for pattern, description in self.patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True, description
        
        return False, None


class PathTraversalDetector(AttackDetector):
    """目录遍历攻击检测器"""
    
    def __init__(self):
        super().__init__()
        self.attack_type = "path_traversal"
        self.attack_category = "access_control"
        self.severity = "high"
        
        self.patterns = [
            (r'\.\./\.\./\.\./etc/passwd', '../../../etc/passwd'),
            (r'\.\./\.\./etc/shadow', '../../etc/shadow'),
            (r'\.\./\.\./windows/system32', '../../windows/system32'),
            (r'\.\.[\\/]\.\.[\\/]', '../.. 路径遍历'),
            (r'%2e%2e[/\\]', 'URL编码 ../ 遍历'),
            (r'%252e%252e[/\\]', '双重URL编码遍历'),
            (r'\.\.%2f', '混合编码遍历'),
            (r'\.\.%5c', '反斜杠编码遍历'),
            (r'/etc/passwd', '直接访问 /etc/passwd'),
            (r'/etc/shadow', '直接访问 /etc/shadow'),
            (r'C:\\Windows\\System32', 'Windows系统目录'),
            (r'C:\\boot\.ini', 'Windows boot.ini'),
            (r'/proc/self/environ', 'Linux进程环境'),
            (r'/var/log/', '日志文件访问'),
            (r'\.\.\\\.\.\\', 'Windows路径遍历'),
            (r'file:///', 'file协议访问'),
        ]
    
    def detect(self, content: str) -> Tuple[bool, Optional[str]]:
        if not content:
            return False, None
        
        for pattern, description in self.patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True, description
        
        return False, None


class RateLimitDetector:
    """频率限制检测器（用于检测暴力破解和DoS）"""
    
    def __init__(self, flask_app, db_instance):
        self.app = flask_app
        self.db = db_instance
        self.thresholds = {
            'login': {'requests': 5, 'window': 60, 'severity': 'high'},  # 1分钟5次
            'api': {'requests': 30, 'window': 60, 'severity': 'medium'},  # 1分钟30次
            'general': {'requests': 100, 'window': 60, 'severity': 'low'},  # 1分钟100次
        }
    
    def check_rate_limit(self, ip: str, endpoint: str) -> Tuple[bool, str, int]:
        """
        检查频率限制
        返回: (是否超限, 攻击类型, 当前请求数)
        """
        from .models import RateLimitLog
        
        # 确定端点类型
        endpoint_type = 'general'
        if 'login' in endpoint.lower():
            endpoint_type = 'login'
        elif '/api/' in endpoint:
            endpoint_type = 'api'
        
        threshold_config = self.thresholds[endpoint_type]
        window_seconds = threshold_config['window']
        max_requests = threshold_config['requests']
        
        with self.app.app_context():
            # 清理过期记录
            cutoff_time = datetime.utcnow() - timedelta(seconds=window_seconds)
            RateLimitLog.query.filter(
                RateLimitLog.timestamp < cutoff_time
            ).delete()
            
            # 统计当前时间窗口内的请求数
            recent_count = RateLimitLog.query.filter(
                RateLimitLog.ip == ip,
                RateLimitLog.endpoint == endpoint,
                RateLimitLog.timestamp >= cutoff_time
            ).count()
            
            # 记录本次请求
            log = RateLimitLog(ip=ip, endpoint=endpoint)
            self.db.session.add(log)
            self.db.session.commit()
            
            recent_count += 1
            
            if recent_count > max_requests:
                attack_type = 'brute_force' if endpoint_type == 'login' else 'dos'
                return True, attack_type, recent_count
            
            return False, '', recent_count


class AttackDetectorManager:
    """攻击检测管理器，统一管理所有检测器"""
    
    def __init__(self, flask_app=None, db_instance=None):
        self.detectors = {
            'xss': XSSDetector(),
            'sqli': SQLInjectionDetector(),
            'cmdi': CommandInjectionDetector(),
            'path_traversal': PathTraversalDetector(),
        }
        
        if flask_app and db_instance:
            self.rate_limiter = RateLimitDetector(flask_app, db_instance)
        else:
            self.rate_limiter = None
    
    def detect_all(self, content: str) -> Dict:
        """
        对内容进行全面检测
        返回: {
            'detected': bool,
            'attacks': [{'type': str, 'category': str, 'severity': str, 'description': str}]
        }
        """
        result = {
            'detected': False,
            'attacks': []
        }
        
        for detector_name, detector in self.detectors.items():
            is_attack, description = detector.detect(content)
            if is_attack:
                result['detected'] = True
                result['attacks'].append({
                    'type': detector.attack_type,
                    'category': detector.attack_category,
                    'severity': detector.severity,
                    'description': description or f'{detector_name} 攻击'
                })
        
        return result
    
    def get_attack_categories(self) -> Dict:
        """获取攻击分类信息"""
        return {
            'injection': {
                'name': '注入类攻击',
                'icon': '💉',
                'types': ['xss', 'sqli', 'cmdi'],
                'description': '通过注入恶意代码来操纵应用程序行为'
            },
            'access_control': {
                'name': '访问控制攻击',
                'icon': '🚫',
                'types': ['path_traversal'],
                'description': '试图访问未授权的资源或文件'
            },
            'behavioral': {
                'name': '行为分析攻击',
                'icon': '⏱️',
                'types': ['brute_force', 'dos'],
                'description': '通过异常行为模式进行的攻击'
            }
        }
