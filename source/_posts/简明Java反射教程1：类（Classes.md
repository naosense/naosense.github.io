---
title: 简明Java反射教程1：类（Classes）
date: 2020-03-07 11:44:19
categories:
tags: [Java,反射]
---

Java反射历来是迈入高级Java开发者的必备科目，网上教程是五花八门，有的失于不够全面，有的失于谬误百出。看过之后不懂的更不懂了，懂得也有点蒙了，偶然看到Oracle的官方教程页面，仿佛打开了新的世界，里面的教程不仅简明易懂而且非常权威，毕竟是官方出品，里面有篇[反射](https://docs.oracle.com/javase/tutorial/reflect/index.html)教程，非常不错，翻译一下，推荐给大家。由于篇幅相对于一篇博客来说还是有点长了，我将其分为三个部分：类､成员以及数组和枚举类型。本篇是第一篇，类的反射。

## 反射用途

反射通常用来修改Java虚拟机应用程序的运行时行为。这是一个相对高级的功能，只应由对语言基础有很深了解的开发人员使用。考虑到这一点，反射是一种强大的技术，可以使应用程序执行原本不可能的操作。

### 扩展功能

应用程序可以通过使用其完全限定名创建外部用户定义类的实例。

### 类浏览器和可视化开发环境

类浏览器需要枚举类的成员。可视化开发环境可以利用反射中可用的类型信息来帮助开发人员编写正确的代码。

### 调试和测试工具

调试工具需要检查类的私有成员。测试工具可以利用反射来系统地调用在类上定义的可发现的API集合，以确保代码的高覆盖率。

## 反射弊端

反射功能强大，但不应任意使用。如果可以在不使用反射的情况下实现需要的操作，那么最好避免使用它。通过反射访问代码时应牢记以下问题。

### 性能开销

由于反射涉及动态解析的类型，因此无法执行某些Java虚拟机优化。因此，反射操作的性能要比非反射操作慢，因此，在性能敏感的应用程序中经常调用的代码段中，应避免使用反射。

### 安全限制

反射需要运行时许可，而在安全管理器下运行时可能不存在这种许可。对于必须在受限的安全上下文（例如Applet）中运行的代码，这是一个重要的考虑因素。

### 内部暴露

由于反射允许执行在非反射代码中非法的操作，例如访问私有字段和方法，因此使用反射可能会导致意外的副作用，这可能会使代码无法正常工作并可能破坏可移植性。反射代码破坏了抽象，因此可能会随着平台的升级而改变行为。

## 教程章节

本教程涵盖了反射在访问和操作类、字段、方法和构造函数方面的常见用法。每节课均包含代码示例，技巧和故障排除信息。

主要章节为：

- [**类**](https://docs.oracle.com/javase/tutorial/reflect/class/index.html)
- [**成员**](https://docs.oracle.com/javase/tutorial/reflect/member/index.html)
- [**数组和枚举类型**](https://docs.oracle.com/javase/tutorial/reflect/special/index.html)

### 类

本课说明了获取[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)对象并使用它检查类的属性的各种方法，包括其声明和内容。

类型要么是引用类型，要么是原始类型。类，枚举和数组（都继承自[`java.lang.Object`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html)）以及接口都是引用类型。引用类型包括[`java.lang.String`](https://docs.oracle.com/javase/8/docs/api/java/lang/String.html)，原始类型的所有包装器类，例如[`java.lang.Double`](https://docs.oracle.com/javase/8/docs/api/java/lang/Double.html)，接口 [`java.io.Serializable`](https://docs.oracle.com/javase/8/docs/api/java/io/Serializable.html)和枚举[`javax.swing.SortOrder`](https://docs.oracle.com/javase/8/docs/api/javax/swing/SortOrder.html)。原始类型有：布尔值(`boolean`)，字节(`byte`)，短型(`short`)，整数(`int`)，长型(`long`)，字符(`char`)，浮点型(`float`)和双精度型(`double`)。

对于每种类型的对象，Java虚拟机都会实例化一个不可变的[`java.lang.Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)实例，该实例提供检查对象的运行时属性（包括其成员和类型信息）的方法。[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)还提供了创建类和对象的能力。最重要的是，它是所有反射API的入口点。本课涵盖了涉及类的最常见的反射操作：

- 获取类对象描述了获取类的方式。
- 检查类修饰符和类型显示如何访问类声明信息。
- 发现类成员说明了如何在类中列出构造函数，字段，方法和嵌套类。
- 故障排除描述了使用类时遇到的常见错误。

#### 获取类对象

所有反射操作的入口点是[`java.lang.Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)。除了[`java.lang.reflect.ReflectPermission`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/ReflectPermission.html)之外，[`java.lang.reflect`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/package-summary.html)包下的所有类都没有公共构造函数。要获得这些类，必须在[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)上调用相应的方法。根据代码是否可以访问对象，类的名称，类型或现有的类，有几种获取类的方法。

##### `Object.getClass()`

如果对象的实例可用，则获取其类的最简单方法是调用[`Object.getClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html#getClass--)。当然，这仅适用于全部继承自[`Object`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html)的引用类型。以下是一些示例。

```java
Class c = "foo".getClass();
```

返回字符串(`String`)的类(`Class`)

```java
Class c = System.console().getClass();
```

与虚拟机关联的唯一控制台由静态方法[`System.console()`](https://docs.oracle.com/javase/8/docs/api/java/lang/System.html#console--)返回。[`getClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html#getClass--)返回的值是与[`getClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html#getClass--)对应的[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)。

```java
enum E { A, B }
Class c = A.getClass();
```

`A`是枚举`E`的实例；因此，[`getClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html#getClass--)返回与枚举类型`E`相对应的[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)。

```java
byte[] bytes = new byte[1024];
Class c = bytes.getClass();
```

由于数组是对象(`Object`)，因此也可以在数组的实例上调用[`getClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html#getClass--)。返回的[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)对应于组件类型为`byte`的数组。

```java
import java.util.HashSet;
import java.util.Set;

Set<String> s = new HashSet<String>();
Class c = s.getClass();
```

在这种情况下，[`java.util.Set`](https://docs.oracle.com/javase/8/docs/api/java/util/Set.html)是类型为[`java.util.HashSet`](https://docs.oracle.com/javase/8/docs/api/java/util/HashSet.html)的对象的接口。[`getClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html#getClass--)返回的值是对应于[`java.util.HashSet`](https://docs.oracle.com/javase/8/docs/api/java/util/HashSet.html)的类。

##### `.class`

如果类的实例不可用，那么可以使用`.class`的方式获取[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)。这也是基本类型获取[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)最简单的方式。

```java
boolean b;
Class c = b.getClass();   // compile-time error

Class c = boolean.class;  // correct
```

请注意，语句`boolean.getClass()`会产生编译时错误，因为布尔值是基本类型且无法取消引用。`.class`语法返回与布尔类型相对应的[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)。

```java
Class c = java.io.PrintStream.class;
```

变量`c`是与类型[`java.io.PrintStream`](https://docs.oracle.com/javase/8/docs/api/java/io/PrintStream.html)对应的[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)。

```java
Class c = int[][][].class;
```

`.class`语法可用于获取多维数组相对应的[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)。

##### `Class.forName()`

如果一个类的完全限定名可用，可以使用静态方法[`Class.forName()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#forName-java.lang.String-)获取相应的[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)。数组的完全限定名不能用于基本类型。数组的限定名可以使用[`Class.getName()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getName--)获取。[`Class.getName()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getName--)适用于引用和基本类型。

```java
Class c = Class.forName("com.duke.MyLocaleServiceProvider");
```

该语句将从给定的完全限定名称创建一个类。

```java
Class cDoubleArray = Class.forName("[D");

Class cStringArray = Class.forName("[[Ljava.lang.String;");
```

变量`cDoubleArray`对应于基本类型为`double`的数组的[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)（即与`double[].class`相同）。变量`cStringArray`对应`String`二维数组的[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)（和`String[][].class`一样）。

##### 基本类型包装类的类型

对于基本类型，`.class`是最容易的一种方式，不过还有一种方式可以获取[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)。每个基本类型和`void`在[`java.lang`](https://docs.oracle.com/javase/8/docs/api/java/lang/package-summary.html)中都有一个包装器类，用于将原始类型装箱到引用类型。每个包装器类都包含一个名为`TYPE`的字段，该字段对应于包装的基本类型的[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)。

```java
Class c = Double.TYPE;
```

有一个类[`java.lang.Double`](https://docs.oracle.com/javase/8/docs/api/java/lang/Double.html)，用于在需要[`Object`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html)时包装基本类型`double`。 [`Double.TYPE`](https://docs.oracle.com/javase/8/docs/api/java/lang/Double.html#TYPE)的值与`double.class`的值相同。

```java
Class c = Void.TYPE;
```

[`Void.TYPE`](https://docs.oracle.com/javase/8/docs/api/java/lang/Void.html#TYPE)与`void.class`相同。

##### 返回`Class`的方法

[`Class.getSuperclass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getSuperclass--)

返回给定类的超类。

```java
Class c = javax.swing.JButton.class.getSuperclass();
```

`javax.swing.JButton`的超类是`javax.swing.AbstractButton`。

[`Class.getClasses()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getClasses--)

返回属于该类成员的所有公共类，接口和枚举，包括继承的成员。

```java
Class<?>[] c = Character.class.getClasses();
```

[`Character`](https://docs.oracle.com/javase/8/docs/api/java/lang/Character.html) 包含两个成员类 [`Character.Subset`](https://docs.oracle.com/javase/8/docs/api/java/lang/Character.Subset.html) 和[`Character.UnicodeBlock`](https://docs.oracle.com/javase/8/docs/api/java/lang/Character.UnicodeBlock.html)。

[`Class.getDeclaredClasses()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getDeclaredClasses--)

返回所有类接口，以及在该类中显式声明的枚举。

```java
Class<?>[] c = Character.class.getDeclaredClasses();
```

[`Character`](https://docs.oracle.com/javase/8/docs/api/java/lang/Character.html)包含两个公共成员类： [`Character.Subset`](https://docs.oracle.com/javase/8/docs/api/java/lang/Character.Subset.html)和[`Character.UnicodeBlock`](https://docs.oracle.com/javase/8/docs/api/java/lang/Character.UnicodeBlock.html)，一个私有类：`Character.CharacterCache`。

[`Class.getDeclaringClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getDeclaringClass--)
[`java.lang.reflect.Field.getDeclaringClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/Field.html#getDeclaringClass--)
[`java.lang.reflect.Method.getDeclaringClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/Method.html#getDeclaringClass--)
[`java.lang.reflect.Constructor.getDeclaringClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/Constructor.html#getDeclaringClass--)

返回这些成员的声明类。 匿名类没有声明类但但有封闭类。

```java
import java.lang.reflect.Field;

Field f = System.class.getField("out");
Class c = f.getDeclaringClass(); // System
```

字段 [`out`](https://docs.oracle.com/javase/8/docs/api/java/lang/System.html#out)是在[`System`](https://docs.oracle.com/javase/8/docs/api/java/lang/System.html)中声明的。

```java
public class MyClass {
    static Object o = new Object() {
        public void m() {} 
    };
    static Class<c> = o.getClass().getEnclosingClass();
}
```

`o`代表的匿名类的声明类为`null`。

[`Class.getEnclosingClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getEnclosingClass--)

返回该类的直接封闭类。

```java
Class c = Thread.State.class().getEnclosingClass();
```

枚举`Thread.State`的封闭类是`Thread`。

```java
public class MyClass {
    static Object o = new Object() { 
        public void m() {} 
    };
    static Class<c> = o.getClass().getEnclosingClass();
}
```

`o`定义的匿名类包含在`MyClass`中。

#### 检查类的修饰符和类型

一个类在声明时可能会有一个或多个修饰符影响它的运行时行为：

- 访问修饰符：`public`,`protected`,`private`
- 需要覆盖的修饰符：`abstract`
- 仅限一个实例的修饰符：`static`
- 禁止修改值的修饰符：`final`
- 执行严格浮点行为的修饰符：`strictfp`
- 注解

并非所有类都允许使用所有修饰符，例如，接口不能为`final`，而枚举不能为`abstract`。[`java.lang.reflect.Modifier`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/Modifier.html)包含所有可能的修饰符的声明。它还包含用于解码[`Class.getModifiers()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getModifiers--)返回的修饰符集的方法。

[`ClassDeclarationSpy`](https://docs.oracle.com/javase/tutorial/reflect/class/example/ClassDeclarationSpy.java)示例演示如何获取类的声明组件，包括修饰符，泛型类型参数，已实现的接口和继承路径。由于[`Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html) 实现了[`java.lang.reflect.AnnotatedElement`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/AnnotatedElement.html)接口，因此也可以查询运行时注解。

```java
import java.lang.annotation.Annotation;
import java.lang.reflect.Modifier;
import java.lang.reflect.Type;
import java.lang.reflect.TypeVariable;
import java.util.Arrays;
import java.util.ArrayList;
import java.util.List;
import static java.lang.System.out;

public class ClassDeclarationSpy {
    public static void main(String... args) {
        try {
            Class<?> c = Class.forName(args[0]);
            out.format("Class:%n  %s%n%n", c.getCanonicalName());
            out.format("Modifiers:%n  %s%n%n",
                   Modifier.toString(c.getModifiers()));

            out.format("Type Parameters:%n");
            TypeVariable[] tv = c.getTypeParameters();
            if (tv.length != 0) {
            out.format("  ");
            for (TypeVariable t : tv)
                out.format("%s ", t.getName());
            out.format("%n%n");
            } else {
            out.format("  -- No Type Parameters --%n%n");
            }

            out.format("Implemented Interfaces:%n");
            Type[] intfs = c.getGenericInterfaces();
            if (intfs.length != 0) {
            for (Type intf : intfs)
                out.format("  %s%n", intf.toString());
            out.format("%n");
            } else {
            out.format("  -- No Implemented Interfaces --%n%n");
            }

            out.format("Inheritance Path:%n");
            List<Class> l = new ArrayList<Class>();
            printAncestor(c, l);
            if (l.size() != 0) {
            for (Class<?> cl : l)
                out.format("  %s%n", cl.getCanonicalName());
            out.format("%n");
            } else {
            out.format("  -- No Super Classes --%n%n");
            }

            out.format("Annotations:%n");
            Annotation[] ann = c.getAnnotations();
            if (ann.length != 0) {
            for (Annotation a : ann)
                out.format("  %s%n", a.toString());
            out.format("%n");
            } else {
            out.format("  -- No Annotations --%n%n");
            }

            // production code should handle this exception more gracefully
        } catch (ClassNotFoundException x) {
            x.printStackTrace();
        }
    }

    private static void printAncestor(Class<?> c, List<Class> l) {
        Class<?> ancestor = c.getSuperclass();
        if (ancestor != null) {
            l.add(ancestor);
            printAncestor(ancestor, l);
        }
    }
}
```

下面是输出的一些样本。用户输入以斜体显示。

$ *`java ClassDeclarationSpy java.util.concurrent.ConcurrentNavigableMap`*

```
Class:
  java.util.concurrent.ConcurrentNavigableMap

Modifiers:
  public abstract interface

Type Parameters:
  K V

Implemented Interfaces:
  java.util.concurrent.ConcurrentMap<K, V>
  java.util.NavigableMap<K, V>

Inheritance Path:
  -- No Super Classes --

Annotations:
  -- No Annotations --
```

这是实际的源代码 [`java.util.concurrent.ConcurrentNavigableMap`](https://docs.oracle.com/javase/8/docs/api/java/util/concurrent/ConcurrentNavigableMap.html)中的实际声明：

```java
public interface ConcurrentNavigableMap<K,V>
    extends ConcurrentMap<K,V>, NavigableMap<K,V>
```

注意，由于这是一个接口，因此它是隐式`abstract`的。编译器为每个接口添加此修饰符。另外，此声明包含两个泛型参数K和V。示例代码仅打印这些参数的名称，但是可以使用[`java.lang.reflect.TypeVariable`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/TypeVariable.html)中的方法获取有关它们的其他信息。接口也可以实现其他接口，如上所示。

$ *`java ClassDeclarationSpy "[Ljava.lang.String;"`*

```
Class:
  java.lang.String[]

Modifiers:
  public abstract final

Type Parameters:
  -- No Type Parameters --

Implemented Interfaces:
  interface java.lang.Cloneable
  interface java.io.Serializable

Inheritance Path:
  java.lang.Object

Annotations:
  -- No Annotations --
```

由于数组是运行时对象，因此所有类型信息均由Java虚拟机定义。特别是，数组实现 [`Cloneable`](https://docs.oracle.com/javase/8/docs/api/java/lang/Cloneable.html)和 [`java.io.Serializable`](https://docs.oracle.com/javase/8/docs/api/java/io/Serializable.html) ，其直接超类始终是[`Object`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html)。

$ *`java ClassDeclarationSpy java.io.InterruptedIOException`*

```
Class:
  java.io.InterruptedIOException

Modifiers:
  public

Type Parameters:
  -- No Type Parameters --

Implemented Interfaces:
  -- No Implemented Interfaces --

Inheritance Path:
  java.io.IOException
  java.lang.Exception
  java.lang.Throwable
  java.lang.Object

Annotations:
  -- No Annotations --
```

从继承路径可以推断出[`java.io.InterruptedIOException`](https://docs.oracle.com/javase/8/docs/api/java/io/InterruptedIOException.html)是一个检查的异常，因为[`RuntimeException`](https://docs.oracle.com/javase/8/docs/api/java/lang/RuntimeException.html) 没有出现。

$ *`java ClassDeclarationSpy java.security.Identity`*

```
Class:
  java.security.Identity

Modifiers:
  public abstract

Type Parameters:
  -- No Type Parameters --

Implemented Interfaces:
  interface java.security.Principal
  interface java.io.Serializable

Inheritance Path:
  java.lang.Object

Annotations:
  @java.lang.Deprecated()
```

输出表明[`java.security.Identity`](https://docs.oracle.com/javase/8/docs/api/java/security/Identity.html)拥有注释[`java.lang.Deprecated`](https://docs.oracle.com/javase/8/docs/api/java/lang/Deprecated.html)是一个不推荐使用的API。反射代码可以使用它来检测已弃用的API。

注意：并非所有注释都可以通过反射获得。只有具有[`RUNTIME`](https://docs.oracle.com/javase/8/docs/api/java/lang/annotation/RetentionPolicy.html#RUNTIME)的[`java.lang.annotation.RetentionPolicy`](https://docs.oracle.com/javase/8/docs/api/java/lang/annotation/RetentionPolicy.html)的那些注解才可访问。在 [`@Deprecated`](https://docs.oracle.com/javase/8/docs/api/java/lang/Deprecated.html)，[`@Override`](https://docs.oracle.com/javase/8/docs/api/java/lang/Override.html)和[`@SuppressWarnings`](https://docs.oracle.com/javase/8/docs/api/java/lang/SuppressWarnings.html)语言中预定义的三个注释中，只有[`@Deprecated`](https://docs.oracle.com/javase/8/docs/api/java/lang/Deprecated.html)在运行时可用。

#### 发现类成员

类提供了用于访问字段，方法和构造函数的两类方法：枚举这些成员的方法和搜索特定成员的方法。与在超接口和超类中搜索继承的成员的方法相比，直接在类上访问成员方法不太一样。下表总结了所有成员定位方法及其特点。

定位字段的类方法

| Class API                                                    | 是否成员列表？ | 是否包含继承成员？ | 是否包含私有成员？ |
| ------------------------------------------------------------ | -------------- | ------------------ | ------------------ |
| [`getDeclaredField()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getDeclaredField-java.lang.String-) | 否             | 否                 | 是                 |
| [`getField()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getField-java.lang.String-) | 否             | 是                 | 否                 |
| [`getDeclaredFields()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getDeclaredFields--) | 是             | 否                 | 是                 |
| [`getFields()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getFields--) | 是             | 是                 | 否                 |

定位方法的类方法

| Class API                                                    | 是否成员列表？ | 是否包含继承成员？ | 是否包含私有成员？ |
| ------------------------------------------------------------ | -------------- | ------------------ | ------------------ |
| [`getDeclaredMethod()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getDeclaredMethod-java.lang.String-java.lang.Class...-) | 否             | 否                 | 是                 |
| [`getMethod()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getMethod-java.lang.String-java.lang.Class...-) | 否             | 是                 | 否                 |
| [`getDeclaredMethods()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getDeclaredMethods--) | 是             | 否                 | 是                 |
| [`getMethods()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getMethods--) | 是             | 是                 | 否                 |

定位构造方法的类方法

| Class API                                                    | 是否成员列表？ | 是否包含继承成员？ | 是否包含私有成员？ |
| ------------------------------------------------------------ | -------------- | ------------------ | ------------------ |
| [`getDeclaredConstructor()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getDeclaredConstructor-java.lang.Class...-) | 否             | N/A                | 是                 |
| [`getConstructor()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getConstructor-java.lang.Class...-) | 否             | N/A                | 否                 |
| [`getDeclaredConstructors()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getDeclaredConstructors--) | 是             | N/A                | 是                 |
| [`getConstructors()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getConstructors--) | 是             | N/A                | 否                 |

> N/A：构造函数不能继承。

给定一个类名并指出感兴趣的成员，[`ClassSpy`](https://docs.oracle.com/javase/tutorial/reflect/class/example/ClassSpy.java)示例使用`get*s()`方法确定所有公共成员的列表，包括任何继承的成员。

```java
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Member;
import static java.lang.System.out;

enum ClassMember { CONSTRUCTOR, FIELD, METHOD, CLASS, ALL }

public class ClassSpy {
    public static void main(String... args) {
	try {
	    Class<?> c = Class.forName(args[0]);
	    out.format("Class:%n  %s%n%n", c.getCanonicalName());

	    Package p = c.getPackage();
	    out.format("Package:%n  %s%n%n",
		       (p != null ? p.getName() : "-- No Package --"));

	    for (int i = 1; i < args.length; i++) {
		switch (ClassMember.valueOf(args[i])) {
		case CONSTRUCTOR:
		    printMembers(c.getConstructors(), "Constructor");
		    break;
		case FIELD:
		    printMembers(c.getFields(), "Fields");
		    break;
		case METHOD:
		    printMembers(c.getMethods(), "Methods");
		    break;
		case CLASS:
		    printClasses(c);
		    break;
		case ALL:
		    printMembers(c.getConstructors(), "Constuctors");
		    printMembers(c.getFields(), "Fields");
		    printMembers(c.getMethods(), "Methods");
		    printClasses(c);
		    break;
		default:
		    assert false;
		}
	    }

        // production code should handle these exceptions more gracefully
	} catch (ClassNotFoundException x) {
	    x.printStackTrace();
	}
    }

    private static void printMembers(Member[] mbrs, String s) {
        out.format("%s:%n", s);
        for (Member mbr : mbrs) {
            if (mbr instanceof Field)
            out.format("  %s%n", ((Field)mbr).toGenericString());
            else if (mbr instanceof Constructor)
            out.format("  %s%n", ((Constructor)mbr).toGenericString());
            else if (mbr instanceof Method)
            out.format("  %s%n", ((Method)mbr).toGenericString());
        }
        if (mbrs.length == 0)
            out.format("  -- No %s --%n", s);
        out.format("%n");
    }

    private static void printClasses(Class<?> c) {
        out.format("Classes:%n");
        Class<?>[] clss = c.getClasses();
        for (Class<?> cls : clss)
            out.format("  %s%n", cls.getCanonicalName());
        if (clss.length == 0)
            out.format("  -- No member interfaces, classes, or enums --%n");
        out.format("%n");
    }
}
```

这个例子比较紧凑。但是`printMembers()`方法有点尴尬，因为反射最早的实现中就存在[`java.lang.reflect.Member`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/Member.html)接口了，所以后来引入泛型时无法对其进行修改以包含更有用的`getGenericString()`方法。唯一的选择就是如上面那样进行测试和转换，使用独立的方法如`printConstructors()`、`printFields()`、`printMethods()`进行打印。

输出样本及其解释如下。用户输入以斜体显示。

$ *`java ClassSpy java.lang.ClassCastException CONSTRUCTOR`*

```
Class:
  java.lang.ClassCastException

Package:
  java.lang

Constructor:
  public java.lang.ClassCastException()
  public java.lang.ClassCastException(java.lang.String)
```

由于构造函数不能继承，因此找不到在直接超类[`RuntimeException`](https://docs.oracle.com/javase/8/docs/api/java/lang/RuntimeException.html)和其他超类中定义的异常链接机制构造函数（具有 [`Throwable`](https://docs.oracle.com/javase/8/docs/api/java/lang/Throwable.html)参数的那些）。

$ *`java ClassSpy java.nio.channels.ReadableByteChannel METHOD`*

```
Class:
  java.nio.channels.ReadableByteChannel

Package:
  java.nio.channels

Methods:
  public abstract int java.nio.channels.ReadableByteChannel.read
    (java.nio.ByteBuffer) throws java.io.IOException
  public abstract void java.nio.channels.Channel.close() throws
    java.io.IOException
  public abstract boolean java.nio.channels.Channel.isOpen()
```

 [`java.nio.channels.ReadableByteChannel`](https://docs.oracle.com/javase/8/docs/api/java/nio/channels/ReadableByteChannel.html)定义了[`read()`](https://docs.oracle.com/javase/8/docs/api/java/nio/channels/ReadableByteChannel.html#read-java.nio.ByteBuffer-)方法。其余方法是从超接口继承的。通过将`get * s()`替换为`getDeclared * s()`，这个代码稍作修改，就可以只列出那些在类中实际声明的方法。

$ *`java ClassSpy ClassMember FIELD METHOD`*

```
Class:
  ClassMember

Package:
  -- No Package --

Fields:
  public static final ClassMember ClassMember.CONSTRUCTOR
  public static final ClassMember ClassMember.FIELD
  public static final ClassMember ClassMember.METHOD
  public static final ClassMember ClassMember.CLASS
  public static final ClassMember ClassMember.ALL

Methods:
  public static ClassMember ClassMember.valueOf(java.lang.String)
  public static ClassMember[] ClassMember.values()
  public final int java.lang.Enum.hashCode()
  public final int java.lang.Enum.compareTo(E)
  public int java.lang.Enum.compareTo(java.lang.Object)
  public final java.lang.String java.lang.Enum.name()
  public final boolean java.lang.Enum.equals(java.lang.Object)
  public java.lang.String java.lang.Enum.toString()
  public static <T> T java.lang.Enum.valueOf
    (java.lang.Class<T>,java.lang.String)
  public final java.lang.Class<E> java.lang.Enum.getDeclaringClass()
  public final int java.lang.Enum.ordinal()
  public final native java.lang.Class<?> java.lang.Object.getClass()
  public final native void java.lang.Object.wait(long) throws
    java.lang.InterruptedException
  public final void java.lang.Object.wait(long,int) throws
    java.lang.InterruptedException
  public final void java.lang.Object.wait() hrows java.lang.InterruptedException
  public final native void java.lang.Object.notify()
  public final native void java.lang.Object.notifyAll()
```

在上面结果的field部分中，枚举的常量值都列了出来。While these are technically fields, it might be useful to distinguish them from other fields.可以使用[`java.lang.reflect.Field.isEnumConstant()`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/Field.html#isEnumConstant--)达到这个木得。本教程的后续部分[Examining Enums](https://docs.oracle.com/javase/tutorial/reflect/special/enumMembers.html)中示例[`EnumSpy`](https://docs.oracle.com/javase/tutorial/reflect/special/example/EnumSpy.java)给出了一个可能的实现。

在结果的method部分，包含声明类的方法名。因此方法`toString()`是在[`Enum`](https://docs.oracle.com/javase/8/docs/api/java/lang/Enum.html#toString--)中实现的，而不是继承自[`Object`](https://docs.oracle.com/javase/8/docs/api/java/lang/Object.html)。通过使用[`Field.getDeclaringClass()`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/Field.html#getDeclaringClass--)，可以对代码进行修改以使其更加明显。以下片段说明了潜在解决方案的一部分。

```java
if (mbr instanceof Field) {
    Field f = (Field)mbr;
    out.format("  %s%n", f.toGenericString());
    out.format("  -- declared in: %s%n", f.getDeclaringClass());
}
```

#### 故障排除

以下示例显示了在类上使用反射时可能会遇到的典型错误。

##### 编译器警告："Note: ... uses unchecked or unsafe operations"

调用方法时，将检查并可能转换参数值的类型。 [`ClassWarning`](https://docs.oracle.com/javase/tutorial/reflect/class/example/ClassWarning.java) 调用[`getMethod()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getMethod-java.lang.String-java.lang.Class...-)会造成一个未受检异常。

```java
import java.lang.reflect.Method;

public class ClassWarning {
    void m() {
        try {
            Class c = ClassWarning.class;
            Method m = c.getMethod("m");  // warning

            // production code should handle this exception more gracefully
        } catch (NoSuchMethodException x) {
            x.printStackTrace();
        }
    }
}
```

$ *`javac ClassWarning.java`*

```
Note: ClassWarning.java uses unchecked or unsafe operations.
Note: Recompile with -Xlint:unchecked for details.
```

$ *`javac -Xlint:unchecked ClassWarning.java`*

```
ClassWarning.java:6: warning: [unchecked] unchecked call to getMethod
  (String,Class<?>...) as a member of the raw type Class
Method m = c.getMethod("m");  // warning
                      ^
1 warning
```

很多库的方法已经使用泛型声明进行了改进。由于`c`被声明为原始类型（没有类型参数），而[`getMethod()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#getMethod-java.lang.String-java.lang.Class...-)的相应参数是参数化类型，因此发生了未经检查的转换。需要编译器生成警告（参见[*The Java Language Specification, Java SE 7 Edition*](https://docs.oracle.com/javase/specs/jls/se7/html/index.html)的[Unchecked Conversion](https://docs.oracle.com/javase/specs/jls/se7/html/jls-5.html#jls-5.1.9) 和 [Method Invocation Conversion](https://docs.oracle.com/javase/specs/jls/se7/html/jls-5.html#jls-5.3)部分）

有两种可能的解决方案。最好修改c的声明以包含适当的泛型类型。在这种情况下，声明应为：

```java
Class<?> c = warn.getClass();
```

或者，可以使用预定义的注解[`@SuppressWarnings`](https://docs.oracle.com/javase/8/docs/api/java/lang/SuppressWarnings.html)放置在问题语句的前面来明确禁止警告。

```java
Class c = ClassWarning.class;
@SuppressWarnings("unchecked")
Method m = c.getMethod("m");  
// warning gone
```

> Tip：作为一般原则，不应忽略警告，因为警告可能表明存在错误。应适当使用参数化的声明。如果这是不可能的（也许是因为应用程序必须与库供应商的代码进行交互），请使用 [`@SuppressWarnings`](https://docs.oracle.com/javase/8/docs/api/java/lang/SuppressWarnings.html)注释违规行。

##### 构造函数不可访问时的InstantiationException

如果尝试创建该类的新实例并且零参数构造函数不可见，则[`Class.newInstance()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#newInstance--)将引发[`InstantiationException`](https://docs.oracle.com/javase/8/docs/api/java/lang/InstantiationException.html)。 [`ClassTrouble`](https://docs.oracle.com/javase/tutorial/reflect/class/example/ClassTrouble.java)示例说明了生成的堆栈记录。

```java
class Cls {
    private Cls() {}
}

public class ClassTrouble {
    public static void main(String... args) {
	try {
	    Class<?> c = Class.forName("Cls");
	    c.newInstance();  // InstantiationException

        // production code should handle these exceptions more gracefully
	} catch (InstantiationException x) {
	    x.printStackTrace();
	} catch (IllegalAccessException x) {
	    x.printStackTrace();
	} catch (ClassNotFoundException x) {
	    x.printStackTrace();
	}
    }
}
```

$ *`java ClassTrouble`*

```
java.lang.IllegalAccessException: Class ClassTrouble can not access a member of
  class Cls with modifiers "private"
        at sun.reflect.Reflection.ensureMemberAccess(Reflection.java:65)
        at java.lang.Class.newInstance0(Class.java:349)
        at java.lang.Class.newInstance(Class.java:308)
        at ClassTrouble.main(ClassTrouble.java:9)
```

[`Class.newInstance()`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html#newInstance--)行为非常类似于new关键字，new失败方法也会失败。反射中的典型解决方案是利用[`java.lang.reflect.AccessibleObject`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/AccessibleObject.html)类，该类提供了抑制访问控制检查的功能。但是这种方法不适用于本例，因为[`java.lang.Class`](https://docs.oracle.com/javase/8/docs/api/java/lang/Class.html)没有继承[`AccessibleObject`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/AccessibleObject.html)。唯一的解决方式就是修改代码使用继承[`AccessibleObject`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/AccessibleObject.html)的[`Constructor.newInstance()`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/Constructor.html#newInstance-java.lang.Object...-)方法。

> Tip：由于本教程[成员](https://docs.oracle.com/javase/tutorial/reflect/member/index.html)章节[创建新的类实例](https://docs.oracle.com/javase/tutorial/reflect/member/ctorInstance.html) 部分所说的原因，一般情况下，使用[`Constructor.newInstance()`](https://docs.oracle.com/javase/8/docs/api/java/lang/reflect/Constructor.html#newInstance-java.lang.Object...-)会好一些。

更多的栗子参见本教程[成员](https://docs.oracle.com/javase/tutorial/reflect/member/index.html)章节[创建新的类实例](https://docs.oracle.com/javase/tutorial/reflect/member/ctorInstance.html) 部分。
