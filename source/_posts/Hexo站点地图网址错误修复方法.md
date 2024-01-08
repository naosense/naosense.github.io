---
title: Hexo站点地图网址错误修复方法
date: 2022-10-19 15:12:01
categories:
tags: [hexo]
---
最近升级了下hexo，部署的时候发现`sitemap.xml`全失效了，每个网址都增加了一个`%25`字符，比如原本应该是`https://naosense.github.io/2016/08/22/%E5%8A%A0%E5%AF%86%E5%92%8C%E8%A7%A3%E5%AF%86/`变成了如下所示网址，

![invalid_url](invalid_url.png)

原因应该和升级Hexo版本有关系，[网上有一个办法](https://carlos.mynet.tw/%E8%A7%A3%E6%B1%BAhexo%E5%BB%BA%E7%AB%8Bsitemap%E7%9A%84%E9%8C%AF%E8%AA%A4%E7%B6%B2%E5%9D%80%E5%85%A7%E5%AE%B9/)是修改`node_modules/hexo-generator-sitemap/sitemap.xml`的代码，但是我的原则是“用新不用旧，谁的问题谁解决”，看了下hexo-generator-sitemap的版本才1.2.0，最新版已经3.0.1了，果断升级，重新生成`sitemap.xml`，一切正常。
