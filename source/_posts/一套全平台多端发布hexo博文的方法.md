---
title: 一套全平台多端发布hexo博文的方法
date: 2023-11-21 18:51:10
categories:
tags: [Hexo, Github]
---
hexo博客建了好久了，一直以来都有几个痛点：

- 只能电脑发布。在手机日期流行的今天还挺要命的，有时候上一天班真心不想开电脑，电脑不能随时随地使用，比如地铁上。
- 图片的插入不方便。需要找图床，或者保存在同名文件夹中，然后手动再插入markdown文档。
- 换电脑需要重复配置hexo环境，每次都要安装一次nodejs以及一堆依赖，特别是后端程序员，使用nodejs不多，时间一长都忘了咋配置，每次都得百度一番。

最近在twitter上受@lencx_启发，发现一套可以全平台多端发布hexo博文的方法，方案如下：

1. 使用github discussion作为数据源，天然支持分类和tag，还有天生的版本管理功能，如果注重隐私，还可以选择私密仓库。
2. 当发布或修改discussion时，使用github api将discussion同步下来，生成markdown文档。
3. 使用github action创建hexo部署环境，将markdown发布成博文。

github有手机端，支持ios和android，支持上传图片，网页端也是相当的好用，github action透明发布，不用再关心部署环境。

大家也可以举一反三，使用这种方式，同步发布公众号什么的。

整体github action配置为

```yml
name: deploy discussion to hexo blog

on:
  # init workflow
  # push:
  #  branches:
  #    - source
  discussion:
    types: [created, edited]

env:
  # change env here
  GITHUB_NAME: naosense
  GITHUB_EMAIL: pingao777@gmail.com
  GH_TOKEN: ${{ secrets.GH_TOKEN }}
  ACTION_DEPLOY_KEY: ${{ secrets.HEXO_DEPLOY_SECRET }}

jobs:
  sync:
    name: Build
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          ref: 'source'
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11.4
      - name: Get pip cache dir
        id: pip-cache
        run: |
          echo "dir=$(pip cache dir)" >> $GITHUB_OUTPUT
      - name: pip cache
        uses: actions/cache@v3
        with:
          path: ${{ steps.pip-cache.outputs.dir }}
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
      - name: Install python dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        if: steps.pip-cache.outputs.cache-hit != 'true'
      - name: Check discussion if is ready
        id: check_discussion
        run: |
          python deploy.py
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 16.19.0
          cache: 'npm'
      - name: Install hexo and dependencies
        run: |
          npm install -g hexo-cli
          npm install
      - name: Hexo deploy and Commit md file
        run: |
          mkdir -p ~/.ssh/
          echo "$ACTION_DEPLOY_KEY" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan github.com >> ~/.ssh/known_hosts
          git config --global user.email "${{ env.GITHUB_EMAIL }}"
          git config --global user.name "${{ env.GITHUB_NAME }}"
          git add source/_posts
          git commit -m 'sync from discussion' \
          && git push \
          && hexo douban \
          && hexo deploy -g \
          && echo "Done, congrats!" \
          || echo "Oops, something wrong!"
```

有几点需要注意：

1. 需要使用secret配置一个token，变量名为`GH_TOKEN`，用来调用github api。
2. 需要生成一个ssh key，用来部署hexo，配置方法参考[ssh配置](https://makefile.so/2021/11/28/use-github-actions-to-deploy-hexo-blog/)。

这样，你就可以愉快地在地铁里，在被窝里……等任何地方写博客了。
