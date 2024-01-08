---
title: Java的equals和hashCode方法浅谈
date: 2018-07-02 16:20:39
categories:
tags: java
---
## 一、概述

`equals`和`hashCode`作为Java基础经常在面试中提到，比如下面几个问题：

1. `equals`和`==`有什么区别？
2. `equals`和`hashCode`有什么关系？
3. `equals`和`hashCode`如何编写？

对于第一个问题不少人只停留在字符串`equals`比较的是内容，`==`比较的是内存地址，而对`equals`的本质极少过问。第二个问题，大多数都知道答案，也有不少记反了，但是更进一步为什么是那样的关系，就不知道了。对于第三个问题，大部分人一上手就把方法签名写错了，就别谈正确的写出实现了。带着这些问题，接下来谈谈自己的一点理解。

<!--more-->

## 二、equals方法

先来看见`equals`方法的签名，
```java
public boolean equals(Object obj) {
  return (this == obj);
}
```

可以看到入参是`Object`，很多人没有注意到这一点，上来就写错了。equals方法顾名思义就判断对象的相等性，默认实现就是`==`，那么说到二者的区别，个人理解，`equals`方法是一种用户定义的“逻辑等”，而`==`是一种“物理等”，用俗语解释就是，`equals`判断是否相同，`==`判断是否一样。

`equals`方法在编写的时候需要遵循以下原则：

- 自反性
- 对称性
- 传递性
- 一致性

下面展开说一下，

1. 自反性的意思是，对于一个非`null`的对象x，`x.equals(x)`一定为`true`，这是显而易见的，无须赘述。
2. 对称性，对于非`null`对象x、y，`x.equals(y) == true`，当且仅当`y.equals(x) == true`。来看一个来自《Effective Java》的例子，

    ```java
    // Broken - violates symmetry!
    public final class CaseInsensitiveString {
      private final String s;

      public CaseInsensitiveString(String s) {
        this.s = Objects.requireNonNull(s);
      }

      // Broken - violates symmetry!
      @Override public boolean equals(Object o) {
        if (o instanceof CaseInsensitiveString)
          return s.equalsIgnoreCase(
              ((CaseInsensitiveString) o).s);
        if (o instanceof String)  // One-way interoperability!
          return s.equalsIgnoreCase((String) o);
        return false;
      }
      ...  // Remainder omitted
    }
    CaseInsensitiveString cis = new CaseInsensitiveString("Polish");
    String s = "polish";
    List<CaseInsensitiveString> list = new ArrayList<>();
    list.add(cis);
    // true or false
    list.contains(s);
    ```
    在JDK8运行`list.contains(s)`返回`false`，但是有的JDK可能会返回`true`，甚至直接崩溃，所以如果违反了对称性，程序的行为是不可预测的。

3. 传递性，对于非`null`对象x、y、z，如果`x.equals(y) == true`且`y.equals(z) == true`，那么`x.equals(z) == true`。同样是来自《Effective Java》的一个例子，

    ```java
    public class Point {
      private final int x;
      private final int y;

      public Point(int x, int y) {
        this.x = x;
        this.y = y;
      }

      @Override public boolean equals(Object o) {
        if (!(o instanceof Point))
          return false;
        Point p = (Point)o;
        return p.x == x && p.y == y;
      }

      ...  // Remainder omitted
    }

    public class ColorPoint extends Point {
      private final Color color;

      public ColorPoint(int x, int y, Color color) {
        super(x, y);
        this.color = color;
      }

      // Broken - violates transitivity!
      @Override public boolean equals(Object o) {
        if (!(o instanceof Point))
          return false;

        // If o is a normal Point, do a color-blind comparison
        if (!(o instanceof ColorPoint))
          return o.equals(this);

        // o is a ColorPoint; do a full comparison
        return super.equals(o) && ((ColorPoint) o).color == color;
      }

      ...  // Remainder omitted
    }

    ColorPoint p1 = new ColorPoint(1, 2, Color.RED);
    Point p2 = new Point(1, 2);
    ColorPoint p3 = new ColorPoint(1, 2, Color.BLUE);
    ```
    显然`ColorPoint`的`equals`实现违反了传递性，`p1.equals(p2) == p2.equals(p3) != p1.equals(p3)`。假如`Point`有两个子类`ColorPoint`和`SmellPoint`，`colorPoint.equals(smellPoint)`将会导致无限递归，最终导致内存耗尽。引用《Effective Java》的说法，

    > There is no way to extend an instantiable class and add a value component while preserving the equals contract, unless you’re willing to forgo the benefits of object-oriented abstraction.

    这句话的大意是如果你继承扩展一个类，就没法再保持`equals`的原则了，除非放弃使用继承。放弃继承？这不是让我们因噎废食嘛，咦，别说，还真能放弃继承，那就是组合，因为本文的重点是`equals`和`hashCode`就不展开了。

4. 一致性，对于非`null`对象x、y，多次调用`x.equals(y)`返回一致。一致性意味着`equals`方法不要依赖不可靠的变量，这里“可靠”的意思不光意味着“不该变时不变”，还意味着“想获取时能获取到”，比如`java.net.URL`的`equals`实现依赖了ip地址，而网络故障时无法获取ip，这是一个不好的实现。

说了那么多，有人可能会说，哎呀这么多原则顾头不顾尾，都要满足，太难了吧，下面列出实现`equals`的一些tips，照着做实现起来就易如反掌，

1. 使用`==`判断是否为`null`或`this`，如果是前者返回`false`，后者就返回`true`。
2. 使用`instanceof`检测是否是正确的类型，如果不是直接返回`false`，如果是，强制转换为正确的类型，然后比较与“逻辑等”相关的变量。

## 三、hashCode方法

`hashCode`主要用来在Java中哈希数据结构`HashMap`、`HashSet`生成哈希值，`hashCode`的方法签名，

```java
public native int hashCode();
```

默认实现会将对象的内存地址转化为一个整数，因此只有同一个对象`hashCode`才一样，即使两个`equals`返回`true`的对象`hashCode`也不一样，如果不进行重写。和`equals`一样，`hashCode`也需要满足一些原则：

1. 一致性，和`equals`相关的变量没有变化，`hashCode`返回值也不能变化。

2. 两个对象`equals`返回`true`，`hashCode`返回值应该相等。由上面得知，`hashCode`默认实现不满足这一条件，因此任何类如果实现了`equals`就必须实现`hashCode`，确保二者的步调一致，下面来看一个反例，

    ```java
    public class Person {
      private int age;
      private String name;

      public Person(int age, String name) {
        this.age = age;
        this.name = name;
      }

      @Override
        public boolean equals(Object obj) {
          if (obj == null) {
            return false;
          }
          if (obj == this) {
            return true;
          }

          if (obj instanceof Person) {
            Person that = (Person) obj;
            return age == that.age && Objects.equals(name, that.name);
          }

          return false;
        }
    }

    Map<Person, Integer> map = new HashMap<>();
    map.put(new Person(10, "小明"), 1);
    map.get(new Person(10, "小明"));
    ```

    初学者可能觉得最后一条语句会返回1，事实上返回的是`null`，为什么会这样呢？明明将数据放进去了，而数据却像被黑洞吞噬一样，要解释得从`HashMap`的数据结构说起，`HashMap`是由数组和链表组成的一种组合结构，如下图，往里存放时，`hashCode`决定数组的下标，而`equals`用于查找值是否已存在，存在的话替换，否则插入；往外取时，先用`hashCode`找到对应数组下标，然后用`equals`挨个比较直到链表的尾部，找到返回相应值，找不到返回null。再回过头看刚才的问题，先放进去一个`new Person(10, "小明")`，然后取的时候又新建了一个`new Person(10, "小明")`，由于没有重写`hashCode`，这两个对象的`hashCode`是不一样的，存和取的数组下标也就不一样，自然取不出来了。

    ![HashMap数据结构](https://wocanmei-hexo.nos-eastchina1.126.net/Java%E7%9A%84equals%E5%92%8ChashCode%E6%96%B9%E6%B3%95%E6%B5%85%E8%B0%88/hashmap.png)

3. 两个对象`equals`返回`false`，`hashCode`返回值可以相等，但是如果不等的话，可以改进哈希数据结构的性能。这条原则也可以用`HashMap`的数据结构解释，举一个极端的例子，假如`Person`所有对象的`hashCode`都一样，那么`HashMap`内部数组的下标都一样，数据就会进到同一张链表里，这张链表比正常情况下要长的多，而遍历链表是一项耗时的工作，性能也就下来了。

那么如何写一个好的`hashCode`呢？

1. 声明一个变量`int`的变量`result`，将第一个和`equals`相关的实例变量的`hashCode`赋值给它。
2. 然后按照下列规则依次计算剩下的实例变量的`hashCode`值`c`。
    1. 如果是null，设置一个常数，通常为0
    2. 如果是原始类型，使用`Type.hashCode(f)`，`Type`为它们的装箱类型
    3. 如果是数组，如果每一个元素都是相关的，可以使用`Arrays.hashCode`；否则将相关元素看作独立的变量计算
3. 使用`result = 31 * result + c`的形式将每个变量的哈希值组合起来，最后返回`result`。

参考资料：《Effective Java》
