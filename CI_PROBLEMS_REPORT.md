
# 🔍 CI问题检测报告

## 📊 问题统计
- 🚨 关键问题: 5
- ⚠️ 高级问题: 14
- 📝 中级问题: 2
- 📋 总计: 21

## 📋 详细问题列表

### File Problems
1. 📝 **MyPy缓存**
   - 路径: `/home/user/projects/football-predict-system/.mypy_cache`
   - 解决方案: 删除文件: rm -rf /home/user/projects/football-predict-system/.mypy_cache

2. 📝 **Ruff缓存**
   - 路径: `/home/user/projects/football-predict-system/.ruff_cache`
   - 解决方案: 删除文件: rm -rf /home/user/projects/football-predict-system/.ruff_cache


### Security Problems
1. 🚨 **硬编码密码**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/demo/culture_penetration_demo.py`
   - 解决方案: 使用环境变量或配置文件

2. 🚨 **硬编码密码**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/scripts/final_security_cleanup.py`
   - 解决方案: 使用环境变量或配置文件

3. 🚨 **硬编码密钥**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/scripts/final_security_cleanup.py`
   - 解决方案: 使用环境变量或配置文件

4. 🚨 **硬编码令牌**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/scripts/final_security_cleanup.py`
   - 解决方案: 使用环境变量或配置文件

5. 🚨 **硬编码密码**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/scripts/fix_medium_risk_issues.py`
   - 解决方案: 使用环境变量或配置文件


### Template Problems
1. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/aiculture/monitoring_config.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/aiculture/monitoring_config.py

2. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/aiculture/alerting_rules.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/aiculture/alerting_rules.py

3. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/aiculture/core.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/aiculture/core.py

4. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/aiculture/templates/python/{{package_name}}/__init__.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/aiculture/templates/python/{{package_name}}/__init__.py

5. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/aiculture/templates/python/{{package_name}}/cli.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/aiculture/templates/python/{{package_name}}/cli.py

6. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/aiculture/templates/python/{{package_name}}/core.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/aiculture/templates/python/{{package_name}}/core.py

7. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/aiculture/cli_commands/template_commands.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/aiculture/cli_commands/template_commands.py

8. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/scripts/generate_quality_report.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/scripts/generate_quality_report.py

9. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/scripts/performance_analyzer.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/scripts/performance_analyzer.py

10. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/scripts/add_type_hints.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/scripts/add_type_hints.py

11. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/scripts/add_docstrings.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/scripts/add_docstrings.py

12. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/tests/test_templates/python/{{package_name}}/cli.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/tests/test_templates/python/{{package_name}}/cli.py

13. ⚠️ **包含Jinja2模板语法**
   - 路径: `/home/user/projects/football-predict-system/src/aiculture-kit/tests/test_templates/python/{{package_name}}/core.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/src/aiculture-kit/tests/test_templates/python/{{package_name}}/core.py

14. ⚠️ **包含ERB模板语法**
   - 路径: `/home/user/projects/football-predict-system/scripts/ci-problem-detector.py`
   - 解决方案: 检查并清理文件: /home/user/projects/football-predict-system/scripts/ci-problem-detector.py
