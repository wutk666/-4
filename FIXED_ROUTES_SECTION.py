# 这是 routes.py 中从第599行开始需要替换的正确代码
# 请手动复制这部分代码替换 routes.py 中第599行到文件末尾的内容

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
                detection = detector_manager.detect_all(target)
                if detection['detected']:
                    attack_info = detection['attacks'][0]
                    log_attack(ip, target, detection, blocked=False, target_url=request.path, user_agent=request.headers.get('User-Agent', ''))
            
            # 模拟安全的ping执行（靶场环境，不执行真实命令）
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
            
            # 模拟安全的文件访问（仅允许特定目录）
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
