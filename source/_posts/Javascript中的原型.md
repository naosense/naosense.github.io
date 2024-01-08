---
title: Javascript中的原型
date: 2016-03-20 13:28:20
categories:
tags: javascript
---
首先要明确的是，

1. js中的原型是一个对象，而且这个对象是函数(对象)的一个属性，即prototype。
2. 当以构造函数的形式调用函数时，即new一个函数，会创建一个实例对象，这个实例的`__proto__`属性会指向构造函数的prototype，由于原型也是对象，所以它也有一个`__proto__`属性，这个属性指向的是原型对象的构造函数的prototype，这样一步一步上溯到Object.prototype,Object.prototype对象的`__proto__`指向的是null，这就形成了一个锁链一样的东西，称为原型链。如果把原型链看做一条河流那么null就是源头了。注意原型prototype是函数的属性而不是实例的。
3. 当一个函数被创建时，Function构造器产生的函数对象会执行类似的代码：`this.prototype = {constructor: this}`

<!--more-->

下面我们用代码来阐述一下上面的结论，假设有这样一段代码：

```javascript
var Flower = function(name) {this.name = name;}
var f = new Flower("flower");
```
那么这段代码的原型链是什么样子的呢？

![原型链](https://wocanmei-hexo.nos-eastchina1.126.net/Javascript%E4%B8%AD%E7%9A%84%E5%8E%9F%E5%9E%8B/1-prototype.png)

原型链为图中红色虚线，我们用代码验证下我们的猜想，
```javascript
// true
f.__proto__ === Flower.prototype;
// true;
Flower.prototype.__proto__ === Object.prototype;
// true
Object.prototype.__proto__ === null;
```
如果把原型链看做一条河流，那么null那一端就是上游，另一端为下游。我们都知道河流是有方向的，水只能由上游流向下游，而不能相反。

那么这个原型链有什么作用呢？它是js继承系统的基础。上面提到，原型也是一个对象，既然是对象就可以拥有属性和方法，但是这个对象有点特殊，如果你往这个对象里添加了属性和方法，处于下游的对象包括原型都会拥有这个属性和方法，甚至会影响到已有的对象。这有点像你往河里面导入一瓶墨水，那么下游很快就会被染上颜色。

还是老样子，用代码验证下，
```javascript
Object.prototype.nishishui = "wo"
// "wo"
Flower.prototype.nishishui
// "wo"
Flower.nishishui
// "wo"
f.nishishui
// "[object Object]"
f.toString()
```
我们从来没有在Flower和f上定义nishishui这个属性，但是它们都可以访问到。这是怎么回事呢，实际上当f调用nishishui这个属性时，首先检查自身，当然没有，然后通过`__proto__`去Flower.prototype中去找发现也没有，最后，以同样的方法找到Object.prototype，发现这小子原来在这里，当然不能放过了。js正是通过这种方式实现自己的继承，例如上面的toString()方法。不过如果原型链过长，会有潜在的性能问题，这个以后再说吧。
