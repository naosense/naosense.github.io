---
title: Javascript中的this
date: 2016-03-27 23:07:42
categories:
tags: javascript
---
对于js的函数有两个特殊的关键字，this和arguments，后者存储的是函数的参数，类似于一个数组。例如如下的函数，

```javascript
var testArgus = function() {console.log(arguments);}
// [1, 2]
testArgus(1,2)
```

<!--more-->

arguments的含义比较明确，而this就不那么直白了，**this指代的是函数运行时所处的上下文**。这句话有两点需要注意：一是this是在运行时决定的，也就是函数在调用之前this的值是不确定的，二是函数所处的上下文，也就是函数运行时所处的环境。

首先看看什么是上下文，对比下面的代码，注意它们的差别。

```javascript
var o = {testThis: function() {return this;}};
var b = {testThis: function() {return this;}()};
o.testThis();
b.testThis;
```

它们的分别会输出什么？事实上，前者会输出Object，也就是o本身；后者会输出window，也就是全局对象。如果感到疑惑，再看《JavaScript高级程序设计》中的一个例子，

```javascript
window.color = "red";
var o = {color: "blue"};

function sayColor() {
   alert(this.color);
}
// "red"
sayColor();
o.sayColor = sayColor;
// "blue"
o.sayColor();
```

需要明确的是，函数的名字仅仅是一个包含指针的变量而已。即使是在不同的环境中执行，全局的sayColor()和o.sayColor()指向的仍然是同一个函数。前者在全局作用域调用，因此this指向的是window，因此输出"red"，当把这个函数赋给对象o并调用o.sayColor()时，this引用的是对象o，因此会输出"blue"。再回头看上面的代码，匿名函数在b中执行，并没有附加到任何对象，实际上相当于在window中执行，因此返回this，指向的是window。

事实上this有那么一条规律，**如果调用函数时是以构造函数的形式，即new函数的形式，this会指向创建的新变量，如果是以普通函数的形式调用，this指向的是全局变量**。还是老样子，用代码说话。

```javascript
var Flower = function(name) {this.name = name;}
// error
alert(name);
var f1 = Flower("f1");
// "f1"
alert(name);
var f2 = new Flower("f2");
// "f1"
alert(name);
// "f2"
alert(f2.name);
```

根据这条规律，也可以解释为什么b.testThis为什么指向window，匿名函数在b中执行，是以普通函数的形式被调用，因此this指向的是全局变量，即window。

既然说到了this，就不得不提call和apply，js中这两个函数用来改变函数所处的上下文，也就是this的指向。例如上面的代码，

```javascript
window.color = "red";
var o = {color: "blue"};

function sayColor() {
   alert(this.color);
}

// "blue"
sayColor.call(o);
```

call和apply用法一样，只是接受的参数不一样，二者第一个参数都代表新的上下文，call接受逗号分隔的各个参数，apply接受数组形式的参数。要注意到，sayColor并不是o的一个方法，但是通过call我们却可以像使用自身的方法一样来调用一个函数，这提供了极大的灵活性，在各大js库中十分常见。
