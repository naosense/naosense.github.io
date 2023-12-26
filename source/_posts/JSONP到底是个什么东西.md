---
title: Jsonp到底是个什么东西
date: 2018-11-22 18:43:44
categories:
tags: [Jsonp, Javascript]
---

这个世界上有好多事对你来说是模棱两可，可能是这样或者那样的原因你没有动力去了解它，以至于它久久萦绕在你的心头，Jsonp就是这么一件事。今天终于有动力想了解一番，经过一番热火朝天的谷歌百度后，发现Jsonp这东西说起来简单的很啊，我自己用一句话总结就是：**使用script标签进行跨域访问**。由于跨域请求返回的数据和JSON相关，故而得名Jsonp。

<!--more-->

众所周知，javascript有同源策略的限制，是不允许跨域访问的，比如位于a.xxx.com下面的js代码，

```javascript
function print_log(json) {
    console.log(json.name);
}

var xhr = new XMLHttpRequest();
xhr.open('GET', 'http://b.xxx.com/test?callback=print_log', true);
```
假设/test?callback=print_log接口的返回值为：
```javascript
print_log({"name": "小明", "id" : 1823, "rank": 7})
```
/test接口返回了一段js代码，这段代码如果正常执行的话将会打印出“小明”，但是由于同源策略，位于a.xxx.com上的js想请求b.xxx.com上的test接口是无法通过的，这就是常说的“js无法跨域”。有没有办法实现跨域呢，大神们想了各种各样的办法，其中之一就是Jsonp，具体来说就是虽说js不能跨域，但是有个例外，那就是script标签可以，利用script标签的跨域特性访问其他域名上的接口，动态生成一段js代码，这样就绕过了同源策略，实现了跨域访问。具体代码如下，
```javascript
var script = document.createElement('script');
script.setAttribute('src', 'http://b.xxx.com/test?callback=print_log');
```
这实际上相当于执行下面的代码，
```javascript
function print_log(json) {
    console.log(json.name);
}

print_log({"name": "小明", "id" : 1823, "rank": 7})
```
不出意外的话可以看到打印出的“小明”了。
