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

## 首次在新电脑克隆

**关键：保护好本地独有文件，不要覆盖！**

当 `~/.workbuddy` 已存在（WorkBuddy 已运行过），需要克隆配置时，按以下步骤：

```powershell
# 1. 备份本地独有文件（不同步到 Git 的）
mkdir ~/.workbuddy-backup
cp ~/.workbuddy/models.json ~/.workbuddy-backup/ 2>$null
cp ~/.workbuddy/settings.json ~/.workbuddy-backup/ 2>$null
cp ~/.workbuddy/workbuddy.db ~/.workbuddy-backup/ 2>$null

# 2. 备份剩余目录，然后克隆
mv ~/.workbuddy ~/.workbuddy-old
git clone git@github.com:pochuan123/workbuddy-config.git ~/.workbuddy

# 3. 恢复本地独有文件
cp ~/.workbuddy-backup/models.json ~/.workbuddy/ 2>$null
cp ~/.workbuddy-backup/settings.json ~/.workbuddy/ 2>$null
cp ~/.workbuddy-backup/workbuddy.db ~/.workbuddy/ 2>$null

# 4. 清理
rm -rf ~/.workbuddy-backup ~/.workbuddy-old
```

## 注意
- Git SSH 命令已配置为 `C:/PROGRA~1/Git/usr/bin/ssh.exe`
- 仓库地址：git@github.com:pochuan123/workbuddy-config.git
- 代理端口：7897
- **本地独有文件（不同步）**：`models.json`、`settings.json`、`workbuddy.db`
- 克隆时务必先备份这些文件，克隆后恢复，否则自定义模型会被清空
