---
title: Git最小命令集
date: 2023-11-24 18:51:18
categories: 
tags: [github, git]
---
## 背景

git命令有点多，选项就更多了，别说初学者无所适从，作为老鸟，如果长期使用ui界面操作，或者一段时间不用命令行也是晕头转向。我呢，就是常年使用idea的ui界面操作git，突然切换vscode，界面和操作方式和之前idea不太一样，用起来很不适应，只好重新把命令行学起来。命令行有一个好处，无论是vscode，还是idea，抑或是其他的什么ide，都可以“一招吃遍”。

## 前提

大部分企业通常仓库会有一个主分支master，大家基于主分支拉取自己的开发分支，修改代码，然后提交，最后合并到master分支。

## 常规流程

常规流程基本上就是：创建分支——>更新代码——>提交代码——>删除分支。

### 创建分支

```bash
# 查看本地分支
git branch
# 创建本地分支并切换
git branch branch_name origin/master
git checkout branch_name
# 或者一步到位
git checkout -b branch_name origin/master
```

### 更新代码

除非个人仓库可以使用`git pull origin master`，其他多人合作的代码库，我建议一律采用先fetch后rebase的方式更新代码。

```bash
# 拉取最新代码
git fetch origin master
# 查看本地当前代码与远程主库区别，如果只想看commit，去掉-p
git log -p HEAD..origin/master
# 将当前代码变基到远程主库上
git rebase origin/master
```

如果代码rebase有冲突，先解决冲突，然后执行继续变基。

```bash
git rebase --continue
```

### 提交代码

```bash
git status
git add some_code_files
git commit -m "commit message"
git push
```

### 删除分支

```bash
# 删除本地分支
git branch -d branch_name
# 忽略未合并的commit强制删除本地分支
git branch -D branch_name 
# 删除远端分支
git push origin :branch_name
```

## 其他命令

### 回退版本

```bash
# 上个版本
git reset HEAD^
# 上两个版本
git reset HEAD^^
# 或
git reset HEAD~1
git reset HEAD~2
```

回退到某个commit

```bash
# commit id前7位
git reset 69fde2c
```

### 美化commit记录

如果写着写着，突然发现有个代码在上一commit中忘了添加了，想追加进去，那可以使用

```bash
git add forgot_file
# 如果是最后一条可以用
git commit -m "commit msg" --amend
# 如果这些commit已经推送到远端了，要使用force推送覆盖
git push --force-with-lease
```

如果写代码写的比较忘我，提交的也不亦乐乎，可能会形成许多零碎的commit，看着很不美观，这时候你可以

```bash
# 修改最后n个提交
git rebase -i HEAD~n
# 如果这些commit已经推送到远端了，要使用force推送覆盖
git push --force-with-lease
```

### 查看文件或文件夹的变动记录

```bash
git log -p -- src/main.cpp
git log -p -- src/some_path
```

