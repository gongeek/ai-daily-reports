# AI Trends Daily Report Generator

自动从多个AI相关数据源抓取热门内容，生成每日趋势报告并提交到GitHub。

## 数据源

- **Hacker News** - AI/ML相关热门故事
- **Reddit** - r/MachineLearning, r/artificial等版块热帖
- **GitHub Trending** - AI项目趋势
- **Twitter** - 可选，通过RapidAPI（需要API key）

## 功能特性

- 每日自动抓取多个数据源的AI相关内容
- 生成标准Markdown格式的日报
- 自动提交到GitHub仓库
- 支持定时执行（cron job）
- 完整的错误处理和日志记录
- 模块化设计，易于扩展新数据源

## 快速开始

### 1. 安装依赖

```bash
cd ai-daily-report
pip3 install -r requirements.txt --user
```

### 2. 配置

复制配置示例并编辑：

```bash
cp config.example.yaml config.yaml
vim config.yaml  # 填入你的API keys和GitHub仓库地址
```

### 3. 配置Reddit API（可选）

1. 访问 https://www.reddit.com/prefs/apps
2. 创建应用（script类型）
3. 获取client_id和client_secret
4. 填入config.yaml

### 4. 配置GitHub仓库

1. 创建新的GitHub仓库用于存储报告
2. 配置SSH密钥：
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   # 将公钥添加到GitHub
   ```
3. 在config.yaml中设置仓库地址

### 5. 测试运行

```bash
python3 src/main.py
```

### 6. 设置定时任务

添加cron job每天自动执行：

```bash
crontab -e
# 添加以下行（每天早上8点执行）
0 8 * * * cd ~/ai-daily-report && /usr/bin/python3 src/main.py >> logs/cron.log 2>&1
```

## 项目结构

```
ai-daily-report/
├── src/
│   ├── sources/           # 数据源模块
│   │   ├── hackernews.py  # Hacker News抓取
│   │   ├── reddit.py      # Reddit抓取
│   │   ├── github.py      # GitHub Trending
│   │   └── twitter.py     # Twitter（可选）
│   ├── generator.py       # 报告生成器
│   ├── git_handler.py     # Git操作
│   └── main.py            # 主程序
├── reports/               # 报告输出目录
├── logs/                  # 日志目录
├── config.yaml            # 配置文件
└── requirements.txt       # Python依赖
```

## 配置说明

编辑 `config.yaml` 文件：

```yaml
sources:
  hackernews:
    enabled: true
    keywords: [AI, ML, GPT, LLM, "machine learning"]
    max_posts: 20

  reddit:
    enabled: true
    subreddits: [MachineLearning, artificial]
    client_id: YOUR_CLIENT_ID
    client_secret: YOUR_CLIENT_SECRET
    max_posts: 15

  github:
    enabled: true
    languages: [Python, "Jupyter Notebook"]
    keywords: [AI, machine-learning]
    max_repos: 15

github:
  repo_url: git@github.com:username/ai-daily-reports.git
  branch: main
```

## 自定义扩展

添加新的数据源：

1. 在 `src/sources/` 创建新的模块
2. 继承 `BaseSource` 类
3. 实现 `fetch()` 方法
4. 在 `config.yaml` 添加配置
5. 在 `main.py` 注册新源

## 许可证

MIT License

## 注意事项

- 各API有调用限制，请合理设置抓取频率
- 长期运行建议定期归档旧报告
- Reddit API需要注册应用（免费）
- Hacker News和GitHub Trending无需API key