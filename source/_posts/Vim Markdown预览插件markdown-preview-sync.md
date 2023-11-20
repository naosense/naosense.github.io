---
title: Vim Markdown预览插件markdown-preview-sync
date: 2018-07-29 10:24:06
categories:
tags: [vim, markdown]
---

花了大概两个星期整了个Vim预览插件[markdown-preview-sync](https://github.com/naosense/markdown-preview-sync)，主要参考了[Markdown Viewer](https://chrome.google.com/webstore/detail/markdown-viewer/ckkdlimhmcjmikdlpkmbgfkaikojcbjk)和[markdown-preview.vim](https://github.com/iamcco/markdown-preview.vim)这两款插件，感谢这两款插件的作者。

支持如下特性：

- 代码高亮
- MathJax
- 自定义CSS
- GFM-TABLE
- 目录TOC

运行效果如图：

<!--more-->

![效果图](https://wocanmei-hexo.nos-eastchina1.126.net/markdown-preview-sync/mpsync-snapshot.png)

**为了用户体验，预览并不是实时显示的，而是在换行时或保存时**。这一点是有意为之的，毕竟大家对Markdown语法都了如指掌了，只是想偶尔看下效果。相信大家都有这样的体验，眼睛不停的在编辑屏和预览屏来回切换，眼睛很累，同时思路也很容易被打断，而且根据我个人的实验，同步频率太快会影响Vim的流畅性。

最后再啰嗦一句，欢迎大家使用并提出宝贵意见！
