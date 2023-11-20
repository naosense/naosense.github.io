---
title: Maven插件屏蔽第三方包日志的方法
date: 2018-06-01 15:23:04
categories:
tags: [maven, 日志]
---

这几天写了一个Maven插件，里面用到了Zookeeper（下面简称ZK），里面打印出了很多“Client environment...”字样的info信息，看着挺闹心，就想着怎么屏蔽掉，让世界清净点。

<!-- more -->

刚开始认为ZK使用的log4j，那么在工程里建个`resources/log4j.properties`，使用`log4j.logger.org.apache.zookeeper=WARN`的形式来屏蔽掉，结果没起作用。后来又使用`log4j.xml`的形式，也是不行。再后来又用logback，还是不行，感觉把能想到的方法都试试了，统统不管用，真是郁闷。

将要放弃时，忽然想到既然是在Maven插件里，里面的log系统是不是另有一套呢，一看果然不是log4j，而是simplelogger，按着指导修改了`[maven home]\conf\logging\simplelogger.properties`，现在有作用了。

因为插件jenkins部署的时候也要使用，如果要修改部署脚本或者挨个修改Maven的配置文件太麻烦，最好能在当前插件里设置，最后试了一下将`simplelogger.properties`里的配置写到Java系统变量里，果然可以，事情终于圆满解决了，解决方式为添加下面的代码：

```java
System.setProperty("org.slf4j.simpleLogger.log.org.apache.zookeeper", "warn");
```

希望能给有类似需求的人一点参考，不得不感叹下Java的日志系统真是杂乱啊！
