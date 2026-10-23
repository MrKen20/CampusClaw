# CampusClaw

面向中小学的班级 AI 学习平台，使用 React、TypeScript、Go、MySQL 和 Qdrant，支持 Docker Compose 部署。

## 功能

- 内置概念讲解、阅读分析、写作指导、错题复盘四个 AI 应用，教师可维护本班提问模板。
- 教师配置智能体、技能及资料绑定；支持 `SKILL.md` 和包含它的 ZIP 技能包，兼容原有 `.md/.txt` 技能文件。
- 学生可同时开启多个独立流式会话，查看历史、消息时间、资料引用，并删除自己的对话。
- 班级资料支持 `.md/.txt` 上传、分类阅读、编辑、删除及检索；仅使用适用片段，不拼接整个知识库。
- 支持外部 MCP 工具登记、发现、批准、技能绑定、多轮调用及审计；凭据保存在服务端。
- 服务端强制校验身份、角色和班级范围。当前支持文字任务，暂不支持图片作业批改。

## 启动

需要 Docker Desktop。

```bash
cp .env.example .env
# 按示例填写数据库、演示账号、网关和 MCP 配置后启动
docker compose up --build -d
```

`SESSION_SECRET`、`MCP_AUTH_TOKEN`、`MCP_ENCRYPTION_KEY` 可分别运行 `openssl rand -hex 32` 生成。模型名称及地址按课程网关配置填写，真实密钥放入本地 `.env`。

- 系统入口：<http://localhost:8080>，端口可通过 `WEB_PORT` 调整。
- Swagger：<http://localhost:8080/swagger/>，登录前即可访问。
- 数据库和上传文件保存在 Docker 数据卷中。

| 账号 | 角色 | 班级 |
| --- | --- | --- |
| `teacher_a` | 教师 | A |
| `student_a1` | 学生 | A |
| `student_b1` | 学生 | B |

口令由 `.env` 中的 `SEED_TEACHER_PASSWORD`、`SEED_STUDENT_PASSWORD` 设置。

## 验证

前端测试需要 Node.js 22.6+，接口测试需要 Python 3 和已启动的服务。

```bash
node --experimental-strip-types --test frontend/tests/*.test.mjs
python3 scripts/generate_openapi.py --check
python3 apitest/run_all.py --live
```

`--live` 会调用配置的模型网关。设计规约与验证记录位于 `openspec/changes/`，接口细节以 Swagger 为准。
