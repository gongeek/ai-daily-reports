# 部署指南

## 快速开始

项目已经完成初始化并测试通过！生成的首份报告在 `reports/2026-05-29.md`。

## 下一步操作

### 1. 配置Reddit API（可选但推荐）

Reddit API是免费的，可以获取更多AI内容：

1. 访问 https://www.reddit.com/prefs/apps
2. 点击"create another app..."
3. 选择"script"类型
4. 填写：
   - name: AI Daily Report Bot
   - redirect uri: http://localhost:8080
5. 创建后，复制：
   - client_id（在应用名称下方的那串字符）
   - client_secret
6. 编辑 `config.yaml`，填入：
   ```yaml
   sources:
     reddit:
       client_id: 你的client_id
       client_secret: 你的client_secret
   ```

### 2. 配置GitHub仓库

自动提交报告到GitHub：

1. 在GitHub创建一个新仓库（例如：ai-daily-reports）
2. 配置SSH密钥（如果还没有）：
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   cat ~/.ssh/id_rsa.pub  # 复制公钥
   ```
3. 添加公钥到GitHub：https://github.com/settings/ssh/new
4. 测试连接：`ssh -T git@github.com`
5. 添加远程仓库：
   ```bash
   git remote add origin git@github.com:YOUR_USERNAME/ai-daily-reports.git
   ```
6. 或者直接在 `config.yaml` 中设置：
   ```yaml
   github:
     repo_url: git@github.com:YOUR_USERNAME/ai-daily-reports.git
   ```

### 3. 设置定时任务

设置每天自动运行：

```bash
crontab -e
```

添加以下行（每天早上8点执行）：
```bash
0 8 * * * cd ~/ai-daily-report && /usr/bin/python3 src/main.py >> logs/cron.log 2>&1
```

其他时间选项：
- 每天6点：`0 6 * * *`
- 每天10点：`0 10 * * *`
- 每12小时：`0 */12 * * *`

### 4. 测试完整流程

```bash
# 测试生成报告（不提交）
python3 src/main.py --dry-run

# 测试完整流程（包括Git提交）
python3 src/main.py
```

## 数据源说明

### 当前可用数据源

1. **Hacker News** ✅ 已启用
   - 免费API，无需配置
   - 自动抓取AI相关热门故事
   - 当前配置：抓取前20条

2. **GitHub Trending** ✅ 已启用
   - 无需API，直接爬取页面
   - 自动筛选AI相关项目
   - 当前配置：Python/Jupyter Notebook项目

3. **Reddit** ⚠️ 需要配置
   - 需要注册Reddit应用（免费）
   - 目标版块：r/MachineLearning, r/artificial等
   - 配置方法见上方

4. **Twitter** ⚠️ 可选
   - 需要RapidAPI订阅
   - 有免费额度限制
   - 在config.yaml中启用并填入API key

### 自定义关键词过滤

编辑 `config.yaml` 修改关键词：

```yaml
sources:
  hackernews:
    keywords:
      - AI
      - ML
      - GPT
      - LLM
      - "machine learning"
      - "deep learning"
      - "neural network"
      # 添加更多关键词...

  github:
    keywords:
      - AI
      - machine-learning
      - deep-learning
      - NLP
      - GPT
      # 添加更多关键词...
```

## 报告格式

生成的报告包含：
- 📊 Overview：总体统计
- 🔥 Hacker News：AI热门故事
- 💬 Reddit：各版块热帖
- 💻 GitHub Trending：AI项目趋势
- 📈 Summary：关键词分析和亮点总结

报告存储在 `reports/YYYY-MM-DD.md`

## 监控与维护

### 查看日志

```bash
# 查看运行日志
cat logs/daily_report.log

# 查看cron执行日志
cat logs/cron.log
```

### 常见问题

1. **Reddit抓取失败**
   - 检查client_id和client_secret是否正确
   - 确认应用类型为"script"
   - 测试Reddit连接

2. **Git push失败**
   - 检查SSH密钥配置
   - 确认远程仓库地址正确
   - 测试SSH连接：`ssh -T git@github.com`

3. **网络请求失败**
   - 检查服务器网络连接
   - 查看日志中的错误信息
   - 可能是临时网络问题，程序会自动重试

### 归档旧报告

长期运行后，报告文件会增多。可以定期归档：

```bash
# 每月归档
mkdir -p archive/2026-05
mv reports/2026-05-*.md archive/2026-05/

# 或者只保留最近30天
find reports/ -name "*.md" -mtime +30 -delete
```

## 扩展新数据源

添加新数据源的步骤：

1. 在 `src/sources/` 创建新模块文件
2. 继承 `BaseSource` 类
3. 实现 `fetch()` 方法
4. 在 `config.yaml` 添加配置
5. 在 `src/main.py` 的 `initialize_sources()` 注册

## 许可证

MIT License - 可自由使用和修改

## 技术支持

遇到问题请查看：
1. README.md - 项目说明
2. logs/daily_report.log - 详细错误日志
3. 本部署指南

---

**当前项目状态：**
- ✅ 项目已初始化
- ✅ 依赖已安装
- ✅ 测试运行成功
- ✅ Git仓库已创建
- ⏳ 等待配置Reddit API和GitHub远程仓库