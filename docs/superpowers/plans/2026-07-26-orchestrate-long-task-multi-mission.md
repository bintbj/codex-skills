# 多 Mission 隔离实施计划

目标：实现“仓库地址 + mission ID”双重定位，并将每个任务的控制状态隔离到
`.task-orchestrator/missions/<mission-id>/`。

## 1. 共享定位模块与模板

- 新增 `scripts/workspace.py`，集中实现 mission ID 校验、mission 根目录解析、
  repository ID 规范化、Git 元数据读取、分支命名和自动发现。
- 将模板状态升级为 schema v2，包含 `mission_id`、`repository_url`、
  `repository_id`、`base_branch` 和 `working_branch`。
- 初始化脚本改为要求 `--mission`，拒绝缺少 Git remote、非法 ID、重复 mission
  或错误分支。

验证：两个 mission 可以在同一临时仓库创建到不同命名空间；失败不遗留目录。

## 2. 验证、交接与迁移

- 验证器改为要求 `--mission`，校验目录、状态、remote、分支、提交和任务均属于
  同一 mission。
- 交接器改为要求 `--mission`，只归档和重写该 mission 的 handoff，并在结果中
  写入仓库地址与 mission ID。
- 新增显式 `migrate_workspace.py`，将旧单任务布局安全迁入 mission 目录；迁移
  前置失败时不修改文件。

验证：错误 mission、错误 remote、错误分支、脏工作区、重复迁移和旧布局冲突均
  被拒绝；两个 mission 的交接文件互不影响。

## 3. Skill 与文档

- 更新 `SKILL.md`，加入短命令中的 `mission=` / `repo=` 语义、选择优先级、
  新账号 clone/fetch 流程和专属分支规则。
- 更新协议、状态参考和 README，提供安装、初始化、继续、交接、新账号接手、
  多 worktree 和迁移的中文指南。

验证：Skill 结构校验通过，README 中不存在单任务路径示例。

## 4. 自动化测试与发布

- 扩展 `unittest`，覆盖双 mission、ID 安全、remote 规范化、校验隔离、迁移及
  bare remote clone 恢复。
- 运行完整单测、`quick_validate.py` 和工作树检查。
- 提交、推送 `bintbj/codex-skills`，下载已发布版本做一致性验证，再以可恢复备份
  更新本机安装版本。

完成标准：所有测试通过，公开 `main`、工作树和本机安装版本的 Skill 内容一致，
并向用户交付完整中文操作指南。
