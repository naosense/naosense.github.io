---
title: 浅谈Java泛型
date: 2017-11-28 11:03:16
categories:
tags: [java, 泛型]
---

相信每个Java程序员对泛型都不陌生，不少人也用过泛型，但是泛型中确实有些点容易让人迷惑，下面我结合自己的使用经历和理解谈谈对泛型的认识，不求面面俱到，但求切中要害。

<!--more-->

## 一、泛型是什么

引用Java文档的解释，

> A generic type is a generic class or interface that is parameterized over types.

大致的意思就是类型经过参数化的类或接口。

## 二、为什么要泛型

在泛型出现之前你要定义一个存储水果类的列表，你只能这样写，

```java
List fruits = new ArrayList();
Elephant e = new Elephant();
fruits.add(e);
Fruit f = (Fruit) fruits.get(0);
```

虽然定义了一个名叫fruits的列表，但是你里面存大象也没人管你，只有在运行时你试图将列表的元素赋值给一个水果时才会报错。为了更早的发现这种错误，Java在5.0引入了泛型机制(Generics)。有了泛型上面的程序就可以这么写，

```java
List<Fruit> fruits = new ArrayList<Fruit>();
Elephant e = new Elephant();
fruits.add(e);  // Compile error
```

这样当你往水果的列表里塞一个大象时编译器就会报错，而不用等到运行时，而且也避免了显式的转型。

## 三、泛型分类

从程序的层次上，泛型分为泛型类和泛型方法。比如Java中的`ArrayList`类就是一个泛型类，

```java
public class ArrayList<E>
```

而集合工具类`Collections`中的`emptyList`方法就是一个泛型方法，

```java
public static final <T> List<T> emptyList() {
    return (List<T>) EMPTY_LIST;
}
```

到这里其实没什么要说的。

## 四、更进一步

### 1、通配符?

通配符代表的意思应该是“某个或某些具体但不确定的类型”，首先具体的是指将来要用某个具体的类来替换通配符，其次不确定是指当前还确定不了是哪种具体类型。

### 2、边界

边界也就是某种类型的子类型或父类型，即`super`定义的下界和`extends`定义的上界。

### 3、类型擦除

如果用一句话解释就是用不用泛型编译后的代码是一样的，更详细更准确的解释是由于泛型是在Java 5.0引入的，为了兼容老版本的Java，编译器会将泛型参数替换为它的边界（上界），如果有多个边界，只保留最左边的，如果没有边界替换为`Object`，最终保留下来的只有正常的类、接口和方法。

```java
public class GeneralTest<T extends Comparable<T> & Iterable<T> & Serializable> {
    void test1(T t) {
        ...
    }

    <E> void test2(E e) {
        ...
    }
}
```

编译后生成的代码为，

```java
void test1(T);
    descriptor: (Ljava/lang/Comparable;)V

<E> void test2(E);
    descriptor: (Ljava/lang/Object;)V
```

可以看到T的边界有三个`Comparable<T> & Iterable<T> & Serializable`，编译后只保留了`Comparable`，而且`Comparable`的泛型`<T>`也去掉了；`test2`中的E没有边界，它直接被替换为了`Object`，而且`test2`作为泛型方法编译后也没有任何泛型的信息。

### 4、替换原则

一个类型的变量可以接受子类型的变量，一个据有某种参数的方法可以在参数的子类型上调用。这个原则几乎是面向对象编程的基础，它可以让我们这么写代码，

```java
Fruit a = new Apple();
List l = new ArrayList();
```

可以把一个“苹果”赋值给“水果”，可以把`ArrayList`赋值给`List`。

### 5、PECS原则

也就是所谓的Producer Extends, Consumer Super原则，作为生产者时使用`extends`，作为消费者时使用`super`，这条原则其实是替换原则的推论。

```java
List<??> list = Arrays.asList(1, 1.3, 5L);
Number i = list.get(0);

Map<String, ??r> map = new HashMap<>();
map.put("212", 1);
```

比如你想要从`list`中取出的数据可以赋值给一个`Number`，根据替换原则，“一个类型的变量可以接受子类型的变量”，你就得定义`list`中的类型都是`Number`的子类型。那么如何表示一个`Number`的子类型呢，因为`extends`在Java中本来就表示继承的意思，所以很自然的想法就是`? extends Number`，这恰恰就是正确答案。

再比如，你想在`map`值里存储各种数字，根据替换原则，“一个据有某种参数的方法可以在参数的子类型上调用”，也就是你想要`put`方法适用在各种数字类型上，“各种数字类型”是这里的“子类型”，所以你需要定义`map`的值是“各种数字类型”的父类型才可以，表示父类Java中同样有个关键字`super`，所以你可能猜想`? super Number`表示的就是这个意思，没错，答案就是这个。

你可以看到，在两种情况下，确定泛型是替换原则中的子类型还是父类型是关键中的关键。这恰恰就是PECS原则的内容，即作为生产者，将泛型传递给别的变量时，使用`extends`；作为消费者，将别的变量传递给泛型时，使用`super`。

### 6、是泛型方法还是通配符

在泛型中，经常面临的一个抉择就是是使用泛型方法还是使用通配符。比如下面的方法，

```java
interface Collection<E> {
    public boolean containsAll(Collection<?> c);
    public boolean addAll(Collection<? extends E> c);
}
```

如果写成泛型方法，

```java
interface Collection<E> {
    public <T> boolean containsAll(Collection<T> c);
    public <T extends E> boolean addAll(Collection<T> c);
}
```

可以看到类型参数T在方法中只使用了一次，和别的类型参数也没有关系，和函数返回值也没有关系，所以T在这里就显得有点多余。

再看另一个例子，

```java
class Collections {
    public static <T> void copy(List<T> dest, List<? extends T> src) {
    ...
}
```

这里的类型参数T就是必须的了，它表明了源列表和目标列表元素的依赖关系，如果没有一个具体的类型参数，这种依赖没法表述。但是如果你写成下面这个样子，就有点画蛇添足了。

```java
class Collections {
    public static <T, S extends T> void copy(List<T> dest, List<S> src) {
    ...
}
```

可以说，原则就是尽可能的使用通配符，因为它更加精炼，当通配符达不到目的的时候再使用具体的类型参数。
