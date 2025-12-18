"""为命令注入和目录遍历测试页面添加防御开关和IP模拟功能"""

# 命令注入页面更新
cmdi_html = open('app/templates/test_cmdi.html', 'r', encoding='utf-8').read()

# 在目标输入框后添加防御开关和IP模拟
old_cmdi = '''          <button id="pingBtn" class="btn btn-danger btn-sm w-100 mb-3">
            <i class="bi bi-play-circle"></i> 执行 Ping
          </button>'''

new_cmdi = '''          <div class="row mb-3">
            <div class="col-md-6">
              <label class="form-label small">模拟IP地址</label>
              <input type="text" id="simulatedIp" class="form-control form-control-sm" placeholder="留空使用真实IP">
              <small class="text-muted">例: 10.0.0.50</small>
            </div>
            <div class="col-md-6">
              <label class="form-label small">防御开关</label>
              <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="defenseSwitch" checked>
                <label class="form-check-label small" for="defenseSwitch">
                  <span id="defenseSwitchLabel">防御已开启</span>
                </label>
              </div>
              <small class="text-muted">关闭后可查看攻击效果</small>
            </div>
          </div>
          
          <button id="pingBtn" class="btn btn-danger btn-sm w-100 mb-3">
            <i class="bi bi-play-circle"></i> 执行 Ping
          </button>'''

cmdi_html = cmdi_html.replace(old_cmdi, new_cmdi)

# 更新JavaScript - 添加防御开关监听
old_cmdi_js = '''  <script>
    // 点击payload示例自动填充
    document.querySelectorAll('.payload-example').forEach(el => {
      el.addEventListener('click', () => {
        document.getElementById('targetInput').value = el.dataset.payload;
      });
    });

    // 执行Ping
    document.getElementById('pingBtn').addEventListener('click', async () => {
      const target = document.getElementById('targetInput').value;'''

new_cmdi_js = '''  <script>
    // 防御开关切换
    document.getElementById('defenseSwitch').addEventListener('change', (e) => {
      const label = document.getElementById('defenseSwitchLabel');
      if (e.target.checked) {
        label.textContent = '防御已开启';
        label.classList.remove('text-danger');
        label.classList.add('text-success');
      } else {
        label.textContent = '防御已关闭';
        label.classList.remove('text-success');
        label.classList.add('text-danger');
      }
    });
    
    // 点击payload示例自动填充
    document.querySelectorAll('.payload-example').forEach(el => {
      el.addEventListener('click', () => {
        document.getElementById('targetInput').value = el.dataset.payload;
      });
    });

    // 执行Ping
    document.getElementById('pingBtn').addEventListener('click', async () => {
      const target = document.getElementById('targetInput').value;
      const defenseEnabled = document.getElementById('defenseSwitch').checked;
      const simulatedIp = document.getElementById('simulatedIp').value.trim();'''

cmdi_html = cmdi_html.replace(old_cmdi_js, new_cmdi_js)

# 更新fetch请求
old_cmdi_fetch = '''        const r = await fetch('/attack/cmdi/ping', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({target: target})
        });'''

new_cmdi_fetch = '''        const r = await fetch('/attack/cmdi/ping', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            target: target,
            defense_enabled: defenseEnabled,
            simulated_ip: simulatedIp
          })
        });'''

cmdi_html = cmdi_html.replace(old_cmdi_fetch, new_cmdi_fetch)

# 更新结果显示
old_cmdi_result = '''        } else {
          resultEl.className = 'result-box success';
          statusEl.className = 'alert alert-success';
          stateEl.innerHTML = '<i class="bi bi-check-circle"></i> 执行成功';
          
          detailsEl.innerHTML = '<p class="text-success">未检测到命令注入</p>';
          
          resultEl.innerHTML = `
            <div class="alert alert-success mb-2">Ping 执行成功</div>
            <pre style="background: #f8f9fa; padding: 12px; border-radius: 4px; font-size: 12px;">${data.output}</pre>
          `;
        }'''

new_cmdi_result = '''        } else {
          resultEl.className = 'result-box success';
          statusEl.className = 'alert alert-success';
          stateEl.innerHTML = '<i class="bi bi-check-circle"></i> 执行成功';
          
          // 显示防御状态和IP信息
          let statusInfo = '';
          if (!data.defense_enabled) {
            statusInfo = '<div class="alert alert-danger mb-2"><i class="bi bi-shield-slash"></i> <strong>防御已关闭</strong> - 命令未被拦截（靶场环境）</div>';
            detailsEl.innerHTML = '<p class="text-warning">⚠️ 防御关闭，命令已执行（仅在靶场内）</p>';
          } else {
            detailsEl.innerHTML = '<p class="text-success">✓ 未检测到命令注入</p>';
          }
          
          if (data.simulated_ip) {
            statusInfo += `<div class="alert alert-info mb-2"><i class="bi bi-router"></i> 模拟IP: <strong>${data.simulated_ip}</strong></div>`;
          }
          
          resultEl.innerHTML = statusInfo + `
            <div class="alert alert-success mb-2">Ping 执行成功</div>
            <pre style="background: #f8f9fa; padding: 12px; border-radius: 4px; font-size: 12px;">${data.output}</pre>
          `;
        }'''

cmdi_html = cmdi_html.replace(old_cmdi_result, new_cmdi_result)

# 保存命令注入页面
with open('app/templates/test_cmdi.html', 'w', encoding='utf-8') as f:
    f.write(cmdi_html)

print("✓ 命令注入测试页面已更新")

# 目录遍历页面更新
path_html = open('app/templates/test_path_traversal.html', 'r', encoding='utf-8').read()

# 在文件路径输入框后添加防御开关和IP模拟
old_path = '''          <button id="viewBtn" class="btn btn-danger btn-sm w-100 mb-3">
            <i class="bi bi-eye"></i> 查看文件
          </button>'''

new_path = '''          <div class="row mb-3">
            <div class="col-md-6">
              <label class="form-label small">模拟IP地址</label>
              <input type="text" id="simulatedIp" class="form-control form-control-sm" placeholder="留空使用真实IP">
              <small class="text-muted">例: 172.16.0.100</small>
            </div>
            <div class="col-md-6">
              <label class="form-label small">防御开关</label>
              <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="defenseSwitch" checked>
                <label class="form-check-label small" for="defenseSwitch">
                  <span id="defenseSwitchLabel">防御已开启</span>
                </label>
              </div>
              <small class="text-muted">关闭后可查看攻击效果</small>
            </div>
          </div>
          
          <button id="viewBtn" class="btn btn-danger btn-sm w-100 mb-3">
            <i class="bi bi-eye"></i> 查看文件
          </button>'''

path_html = path_html.replace(old_path, new_path)

# 更新JavaScript
old_path_js = '''  <script>
    // 点击payload示例自动填充
    document.querySelectorAll('.payload-example').forEach(el => {
      el.addEventListener('click', () => {
        document.getElementById('pathInput').value = el.dataset.payload;
      });
    });

    // 查看文件
    document.getElementById('viewBtn').addEventListener('click', async () => {
      const filepath = document.getElementById('pathInput').value;'''

new_path_js = '''  <script>
    // 防御开关切换
    document.getElementById('defenseSwitch').addEventListener('change', (e) => {
      const label = document.getElementById('defenseSwitchLabel');
      if (e.target.checked) {
        label.textContent = '防御已开启';
        label.classList.remove('text-danger');
        label.classList.add('text-success');
      } else {
        label.textContent = '防御已关闭';
        label.classList.remove('text-success');
        label.classList.add('text-danger');
      }
    });
    
    // 点击payload示例自动填充
    document.querySelectorAll('.payload-example').forEach(el => {
      el.addEventListener('click', () => {
        document.getElementById('pathInput').value = el.dataset.payload;
      });
    });

    // 查看文件
    document.getElementById('viewBtn').addEventListener('click', async () => {
      const filepath = document.getElementById('pathInput').value;
      const defenseEnabled = document.getElementById('defenseSwitch').checked;
      const simulatedIp = document.getElementById('simulatedIp').value.trim();'''

path_html = path_html.replace(old_path_js, new_path_js)

# 更新fetch请求
old_path_fetch = '''        const r = await fetch('/attack/path/view', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({filepath: filepath})
        });'''

new_path_fetch = '''        const r = await fetch('/attack/path/view', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            filepath: filepath,
            defense_enabled: defenseEnabled,
            simulated_ip: simulatedIp
          })
        });'''

path_html = path_html.replace(old_path_fetch, new_path_fetch)

# 更新结果显示
old_path_result = '''        } else {
          resultEl.className = 'result-box success';
          statusEl.className = 'alert alert-success';
          stateEl.innerHTML = '<i class="bi bi-check-circle"></i> 文件读取成功';
          
          detailsEl.innerHTML = '<p class="text-success">未检测到目录遍历</p>';
          
          resultEl.innerHTML = `
            <div class="alert alert-success mb-2">文件: ${data.filename}</div>
            <pre style="background: #f8f9fa; padding: 12px; border-radius: 4px; font-size: 12px; max-height: 300px; overflow-y: auto;">${data.content}</pre>
          `;
        }'''

new_path_result = '''        } else {
          resultEl.className = 'result-box success';
          statusEl.className = 'alert alert-success';
          stateEl.innerHTML = '<i class="bi bi-check-circle"></i> 文件读取成功';
          
          // 显示防御状态和IP信息
          let statusInfo = '';
          if (!data.defense_enabled) {
            statusInfo = '<div class="alert alert-danger mb-2"><i class="bi bi-shield-slash"></i> <strong>防御已关闭</strong> - 路径未被拦截（靶场环境）</div>';
            detailsEl.innerHTML = '<p class="text-warning">⚠️ 防御关闭，文件访问未被限制（仅在靶场内）</p>';
          } else {
            detailsEl.innerHTML = '<p class="text-success">✓ 未检测到目录遍历</p>';
          }
          
          if (data.simulated_ip) {
            statusInfo += `<div class="alert alert-info mb-2"><i class="bi bi-router"></i> 模拟IP: <strong>${data.simulated_ip}</strong></div>`;
          }
          
          resultEl.innerHTML = statusInfo + `
            <div class="alert alert-success mb-2">文件: ${data.filename}</div>
            <pre style="background: #f8f9fa; padding: 12px; border-radius: 4px; font-size: 12px; max-height: 300px; overflow-y: auto;">${data.content}</pre>
          `;
        }'''

path_html = path_html.replace(old_path_result, new_path_result)

# 保存目录遍历页面
with open('app/templates/test_path_traversal.html', 'w', encoding='utf-8') as f:
    f.write(path_html)

print("✓ 目录遍历测试页面已更新")
print("\n所有测试页面已添加:")
print("  - 防御开关（可关闭防御查看攻击效果）")
print("  - IP模拟（可模拟不同IP发起攻击）")
print("  - 攻击效果展示（仅在靶场内生效）")
