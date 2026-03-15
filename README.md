# Feishu MCP Proxy

飞书 MCP 服务的本地反向代理，自动管理 `tenant_access_token` 的获取和刷新，让你的 AI Agent 无需关心 token 过期问题。

## 架构

```
Claude Code / AI Agent
  │
  │ POST http://localhost:9099/mcp
  ▼
┌─────────────────────────┐
│   Feishu MCP Proxy      │
│   - 自动获取 TAT        │
│   - 后台定时刷新        │
│   - 透明转发请求        │
└─────────────────────────┘
  │
  │ POST https://mcp.feishu.cn/mcp
  │ + X-Lark-MCP-TAT: t-xxx
  ▼
Feishu MCP Server
```

## 前置条件

1. Python 3.10+
2. 在[飞书开放平台](https://open.feishu.cn/app)创建自建应用，获取 **App ID** 和 **App Secret**
3. 为应用申请所需的 API 权限（如 `docx:document:readonly`, `docx:document:create` 等）

## 安装

```bash
git clone https://github.com/Tim-Siu/feishu-mcp-proxy.git
cd feishu-mcp-proxy
pip install .
```

或开发模式安装：

```bash
pip install -e .
```

## 配置

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
FEISHU_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 可选配置

| 环境变量 | 说明 | 默认值 |
|---|---|---|
| `FEISHU_ALLOWED_TOOLS` | 允许的工具列表（逗号分隔） | 全部工具 |
| `PROXY_HOST` | 监听地址 | `localhost` |
| `PROXY_PORT` | 监听端口 | `9099` |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 启动

```bash
python -m feishu_mcp_proxy
```

或使用安装后的命令：

```bash
feishu-mcp-proxy
```

启动后可通过 `/health` 端点检查状态：

```bash
curl http://localhost:9099/health
```

## Claude Code 集成

### 一键配置

```bash
claude mcp add feishu --transport http http://localhost:9099/mcp
```

这会自动将飞书 MCP 添加到你的 Claude Code 配置中。

### 手动配置

也可以在项目目录下创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "feishu": {
      "type": "streamableHttp",
      "url": "http://localhost:9099/mcp"
    }
  }
}
```

启动 proxy 后，Claude Code 即可直接使用飞书 MCP 工具（如 `fetch-doc`, `create-doc`, `search-doc` 等），无需手动管理 token。

## 支持的 MCP 工具

| 工具 | 说明 |
|---|---|
| `search-doc` | 搜索云文档 |
| `create-doc` | 创建云文档 |
| `fetch-doc` | 查看云文档内容 |
| `update-doc` | 更新云文档 |
| `list-docs` | 列出知识空间下的文档 |
| `get-comments` | 查看文档评论 |
| `add-comments` | 添加文档评论 |
| `search-user` | 搜索用户 |
| `get-user` | 获取用户信息 |
| `fetch-file` | 获取文件内容 |

## License

MIT
