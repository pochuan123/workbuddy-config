---
name: workbuddy-sync
description: 同步 WorkBuddy 配置文件。从 GitHub 拉取最新配置到本机，或将本机改动推送到 GitHub。用户说"同步配置""同步一下""拉取配置""推送配置"时触发。
---

# WorkBuddy 配置同步

## 拉取同步（从远程同步到本地）

```powershell
cd ~/.workbuddy
git pull origin main
```

如果拉取成功且有更新，告知用户更新了哪些文件（`git log -1 --oneline --name-only` 查看最近提交的文件列表）。

如果本地有未提交的改动导致冲突：
1. 先 `git stash` 暂存本地改动
2. `git pull`
3. `git stash pop` 恢复本地改动
4. 如果有冲突，告知用户手动解决

## 推送同步（从本地推送到远程）

当用户修改了配置或安装了新 skill 后：

```powershell
cd ~/.workbuddy
git add -A
git status
```

展示将要提交的变更，请用户确认后：

```powershell
git commit -m "update: <简要描述>"
git push origin main
```

## 注意
- Git SSH 命令已配置为 `C:/PROGRA~1/Git/usr/bin/ssh.exe`
- 仓库地址：git@github.com:pochuan123/workbuddy-config.git
- 代理端口：7897
