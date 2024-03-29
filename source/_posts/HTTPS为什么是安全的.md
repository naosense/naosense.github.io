---
title: HTTPS为什么是安全的
date: 2016-08-23 17:08:28
categories:
tags: [http, https]
---

HTTP我们都知道是超文本传输协议，HTTPS与HTTP一字之差，它到底是什么呢？引用《HTTP权威指南》的介绍：
> HTTPS是最常见的HTTP安全版本。它得到了很广泛的应用，所有主要的商业浏览器和服务器上都提供HTTPS。HTTPS将HTTP协议与一组强大的对称、非对称和基于证书的加密技术结合在一起，使得HTTPS不仅很安全，而且很灵活，很容易在处于无序状态的、分散的全球互联网上进行管理。

HTTPS是最常见的HTTP安全版本。多出的S是Security安全的意思，那么它是如何保证安全的呢？

<!--more-->

我们先看看HTTP和HTTPS通信协议层。

![配图来源于《HTTP权威指南》](https://wocanmei-hexo.nos-eastchina1.126.net/HTTPS%E4%B8%BA%E4%BB%80%E4%B9%88%E6%98%AF%E5%AE%89%E5%85%A8%E7%9A%84/1-http%20layer.png)

可以看到，相比HTTP，HTTPS多了一个安全层协议**SSL/TLS**（安全套接层Secure Sockets Layer和传输层安全协议Transport Layer Security，后者是SSL的后继版本），保证安全的秘密就是这个安全层协议。**简单说来，HTTPS就是在安全的传输层上传输报文的HTTP。**

让我们具体看看，SSL包括两部分：记录协议（record protocol）和握手协议（handshake protocol），前者主要定义了数据格式，后者定义了安全传输客户端/服务器需要交换的具体信息，这是我们要介绍的重点。

握手协议包括下面十个步骤：

1. 客户端向服务器发送SSL协议版本、自己支持的加密方式、随机产生的一段数据。
2. 服务器向客户端发送SSL协议版本、根据双方支持的加密方式确定一个最安全的加密方式、随机产生的一段数据以及自己的数字证书。
3. 客户端验证服务器的合法性，如果合法进行下一步，否则会话终止，包括如下过程：
- 数字证书是否过期
- 数字证书是否可信，即证书的颁发机构是否在客户端往往是浏览器的信任列表
- 数字证书的公钥能否验证数字签名，即数字签名的合法性，这个过程参见*[数字签名是什么](https://naosense.github.io/2018/08/15/%E6%95%B0%E5%AD%97%E7%AD%BE%E5%90%8D%E6%98%AF%E4%BB%80%E4%B9%88/)*
- 域名是否与证书的域名匹配

4. 如果第3步中服务器合法，客户端使用使用到目前产生的所有数据为本会话生成一个预置密码（ premaster secret），然后使用服务器的公钥加密预置密码，将密文发送给服务器。
5. 如果服务器要求对客户端进行验证（可选），客户端会将签名数据和证书连同预置密码密文一并发给服务器。
6. 服务器对客户端进行验证，过程与第3步类似。验证不通过会话终止，验证通过，服务器使用私钥解密预置密码，然后执行一系列步骤（客户端会同时执行同样的步骤）生成主密钥（master secret）。
7. 客户端和服务器使用主密钥生成会话密钥（session key），这就是加密后面所有数据的对称密钥。
8. 客户端发送一条消息通知服务器以后的数据都将使用会话密钥加密，然后再发送一条消息表明握手过程的客户端部分完成。
9. 服务器也发送一条消息通知客户端以后的数据都将使用会话密钥加密，然后再发送一条消息表明握手过程的服务器部分完成。
10. 握手过程完成，SSL会话开始使用会话密钥传输数据。

可以看到整个握手过程既包括非对称加密又包括对称加密，先用非对称密钥传送对称密钥，再用对称密钥传送后面的数据，充分利用了两种加密方式的优势，参见*[加密和解密](https://naosense.github.io/2018/08/17/%E5%8A%A0%E5%AF%86%E5%92%8C%E8%A7%A3%E5%AF%86/)*。

回到开头的问题，HTTPS如何保证安全呢？兵法云：知己知彼百战百胜，我们知道互联网安全三大威胁：窃听、篡改和伪装，假如让我们作为攻击者，该如何去做呢？

事实上，上面十个步骤中第1、2步是明文传输的，我们可以对这两步的信息进行拦截得到双方的协议版本、加密方式、随机数以及服务器证书，然后原封不动的将相应信息再发送给对方，我们在通信中间扮演一个伪装者，对客户端来说我们就是服务器，对服务器来说我们就是客户端。现在来到第3步，客户端对我们的攻击全然不知，还把我们当成真正的服务器，客户端验证我们发送给它的数字证书，结果肯定是通过的，因为我们是将服务器的数字证书原封不动的发过去的。接着客户端将预置密码加密然后发送给服务器，这个信息肯定也没法逃脱我们的火眼金睛，但是我们拿过拦截到的信息一看有点傻眼了，由于我们没有服务器密钥，无法进行解密，也就无法得到预置密码，接下来的步骤就无法进行，客户端这时候就反应过来了，等了这么久没反应，对方肯定就问题，会话终止。至于其他的步骤，都是加密数据，窃听篡改没什么意义，这样，三大威胁就被解决了。
