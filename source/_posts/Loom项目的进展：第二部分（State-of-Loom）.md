---
title: "Loom项目的进展：第二部分（State of Loom）"
date: 2020-10-31 12:11:39
categories:
tags: [Java, Loom]
---

[第一部分](https://naosense.github.io/2020/10/11/Loom%E9%A1%B9%E7%9B%AE%E7%9A%84%E8%BF%9B%E5%B1%95%EF%BC%9A%E7%AC%AC%E4%B8%80%E9%83%A8%E5%88%86%EF%BC%88State%20of%20Loom%EF%BC%89/)介绍了虚拟线程并解释了JDK如何适配的去使用它们。随着线程的数量越来越多，生命周期越来越短，管理它们和在它们之间分配工作的新方法属于 Project Loom 的范畴: 在线程之间传递数据的新的灵活机制(比如通道)可能是可取的; 聚集大量线程可以受益于一种被称为**结构化并发(structured concurrency)**的组织和监督方法; 最后，我们正在探索一种比线程局部变量更方便、更有效的构造，用于我们暂时称为**作用域变量(scope variables)**的上下文数据。

和往常一样，如果您能向Loom开发人员邮件列表反馈使用Loom的体验，我们将非常感激。

# 通道

当涉及到线程计算的单个结果的交流时，[`java.util.concurrent.Future`](https://docs.oracle.com/en/java/javase/14/docs/api/java.base/java/util/concurrent/Future.html)就足够了，同时[`CompletableFuture`](https://docs.oracle.com/en/java/javase/14/docs/api/java.base/java/util/concurrent/CompletableFuture.html)类架起了同步世界和异步世界的桥梁：使用thenXXX进行异步操作，使用get进行同步操作。当涉及到多个结果的交流时，[`Flow`](https://docs.oracle.com/en/java/javase/14/docs/api/java.base/java/util/concurrent/Flow.html)类为异步代码提供了一个很好的解决方案。在设计出更多的同步解决方案之前，[`BlockingQueue`](https://docs.oracle.com/en/java/javase/14/docs/api/java.base/java/util/concurrent/BlockingQueue.html)可用于在线程之间通信多个值(特别是 [`LinkedTransferQueue`](https://docs.oracle.com/en/java/javase/14/docs/api/java.base/java/util/concurrent/LinkedTransferQueue.html))。

在一个原型中，通道类型被称为 Carrier，以区别于 NIO 通道。尽管可能会发生变化，但目前看起来是这样的:

```java
Carrier<String> carrier = new Carrier<>();

Thread producer = Thread.startVirtualThread(() -> {
  Carrier.Sink<String> sink = carrier.sink();
  sink.send("message1");
  sink.send("message2");
  sink.closeExceptionally(new InternalError());
});

Thread consumer = Thread.startVirtualThread(() -> {
  try (Carrier.Source<String> source = carrier.source()) {
    while (true) {
      String message = source.receive();
      System.out.println(message);
    }
  } catch (IllegalStateException e) {
    System.out.println("consumer: " + e + " cause: " + e.getCause());
  }
});

producer.join();
consumer.join();
```

# 结构化并发

由于线程代价低廉且数量众多，它们可以从聚集线程的标准实践中获益。我们发现了一个特别吸引人的方法: 结构化并发。

结构化并发将线程生命周期分解为代码块。类似于结构化编程控制将顺序执行的控制流限制在一个定义良好的代码块中，结构化的并发性对并发控制流也是如此。它的基本原则是: 在某个代码单元中创建的线程必须在我们退出该代码单元时全部终止; 如果执行分裂为某个范围内的多个线程，它必须在退出该范围之前合并。特别是，方法在生成可以无限期存活的线程后不应返回。

为了让这个想法更清楚，让我们看一些代码。在我们当前的原型中，我们使用限制子线程生命周期的代码块代表一个结构化并发范围，通过将[`java.util.concurrent.ExecutorService`](https://download.java.net/java/early_access/loom/docs/api/java.base/java/util/concurrent/ExecutorService.html)成为一个**AutoCloseable**，`close`方法用来关闭服务等待终止。这保证了在我们退出try with resources（TWR）块时，提交给executor的所有任务都将终止，并将它们的生命周期限制在代码结构中：

```java
ThreadFactory vtf = Thread.builder().virtual().factory();
try (ExecutorService e = Executors.newUnboundedExecutor(vtf)) {
   e.submit(task1);
   e.submit(task2);
} // blocks and waits
```

在我们退出TWR块之前，当前线程将阻塞，等待所有任务及其线程完成。一旦离开它，我们就可以保证任务已经结束。

因此，我们直接将代码表示成某些过程计算的非常有组织的形式。如果;是顺序组合，|是并行组合，那么我们的代码可以这样描述：**a;(b|((c|d);e));f**，其中连接点（我们等待子线程完成）是并行操作之后和下一个顺序操作之前的右括号，如**(x|y|z);w**。

除了清晰之外，该结构还具有强大的不变性：每个线程（在结构化并发上下文中）都有一些“父”线程，该线程被阻塞以等待其终止，因此应当关心何时（或者如何）执行。它在错误传播和消除方面具有一些强大的优势。

## 结构化中断

非结构化线程脱离了任何上下文或明确的责任。由于结构化线程显然为其父级执行某些工作，因此当取消父级时，也应取消子级。

因此，如果父线程被中断，我们将中断传播给它的子线程。我们还可以给所有任务一个截止期限，在任务到期时中断那些尚未终止的子任务（以及当前线程）：

```java
try (var e = Executors.newUnboundedExecutor(myThreadFactory)
                      .withDeadline(Instant.now().plusSeconds(30))) {
   e.submit(task1);
   e.submit(task2);
}
```

## 结构化错误

非结构化线程可能会遇到异常，并且会在没有任何注意的情况下单独死亡。结构化线程的故障将由其监视的父级观察到，然后可以将故障置于上下文中，例如，通过将子异常的堆栈跟踪与其父级的堆栈跟踪缝合在一起。

但是错误传播带来了一些挑战。假设一个子线程抛出的异常会自动传播到其父节点，结果，该异常将随后取消（中断）父线程的所有其他子线程。在某些情况下，这可能是理想的选择，但是是否应该是默认行为尚不清楚。因此，目前，我们正在尝试更明确的错误和结果处理。

我们可以使用新的[`ExecutorService.submitTasks`](https://download.java.net/java/early_access/loom/docs/api/java.base/java/util/concurrent/ExecutorService.html#submitTasks(java.util.Collection))和[`CompletableFuture.stream`](https://download.java.net/java/early_access/loom/docs/api/java.base/java/util/concurrent/CompletableFuture.html#stream(java.util.Collection))，它将每个任务完成时的结果流化，不管成功与否(也充当到CompletableFuture的异步世界的桥梁)，以等待第一个任务成功完成，然后取消所有其他任务：

```java
try (var e = Executors.newUnboundedVirtualThreadExecutor()) {
  List<CompletableFuture<String>> tasks = e.submitTasks(List.of(
    () -> "a",
    () -> { throw new IOException("too lazy for work"); },
    () -> "b",
  ));

  try {
    String first = CompletableFuture.stream(tasks)
      .filter(Predicate.not(CompletableFuture::isCompletedExceptionally))
      .map(CompletableFuture::join)
      .findFirst()
      .orElse(null);
    System.out.println("one result: " + first);
  } catch (ExecutionException ee) {
    System.out.println("¯\\_(ツ)_/¯");
  } finally {
    tasks.forEach(cf -> cf.cancel(true));
  }
}
```

一些常见模式可以由helper方法提供服务，比如**ExecutorService**的**invokeAll**或**invokeAny**。此示例与上面更详细的示例执行相同的操作：

```java
try (var e = Executors.newUnboundedVirtualThreadExecutor()) {
  String first = e.invokeAny(List.of(
    () -> "a",
    () -> { throw new IOException("too lazy for work"); },
    () -> "b"
  ));
  System.out.println("one result: " + first);
} catch (ExecutionException ee) {
  System.out.println("¯\\_(ツ)_/¯");
}
```

这些API位于EA中，但是随着我们试图使线程管理更加友好，该领域可能会有很多变化。

## 结构化服务性和可观测性

结构化并发不仅有助于组织代码，还有助于在进行概要分析和调试时提供有意义的上下文。一百万个线程的线程dump可能没有用，但是如果可以将这些线程显示在根据结构化并发作用域层次结构排列的树中，则可以更好地理解它们。同样，JFR可以按SC作用域对线程及其执行的操作进行分组，从而可以放大或缩小配置文件。这项工作不太可能进入第一个预览版。

# 作用域变量

有时我们需要以对中间框架透明的方式将某些上下文从调用者传递到被调用者。例如，一个调用链foo`→`bar`→`baz，foo和baz是应用代码，bar是程序库代码，或者反过来，foo希望在没有bar参与的情况下与baz共享数据。目前，这通常是通过线程局部变量`ThreadLocal`来完成的，但是TLs(我们将简称为TLs)有严重的缺点。

一方面，它们的结构与我们上面使用的含义类似：一旦设置了TL值，该值在线程的整个生命周期内有效，或者直到将其设置为其他值为止。实际上，我们通常会看到一种使用模式，试图借用TL结构（不幸的是，没有任何性能优势）：

```java
var oldValue = myTL.get();
myTL.set(newValue);
try {
  ...
} finally {
  myTL.set(oldValue);
}
```

如果没有这种强制性的结构，当在多个任务之间共享线程时，一个任务的TL值可能会泄漏到另一个任务中。虚拟线程通过足够轻量级而无需共享来解决该问题。但是，这种非结构化的特性还意味着TL实现必须依靠弱引用来允许GC清理不再使用的TL，这会使它们的实现速度大大降低。

另一个问题是继承。例如，那些使用像OpenTracing这样的分布式跟踪工具的人，可能想要从父线程继承跟踪“ span”。这可以通过**InheritableThreadLocal**(iTL)实现。创建线程时必须复制线程中的iTL映射，因为iTL是可变的，因此无法共享。这既造成了占用空间又造成了速度上的损失。另外，由于当今的线程是非结构化的，因此当子线程访问其继承的span时，其父级可能已将其关闭。虚拟线程只会加剧iTL继承的问题，因为它们鼓励创建许多小线程，其中一些代表其父线程执行一些小任务，例如单个HTTP请求，从而增加了对iTL继承的需求以及复杂的占用空间和速度成本。

如果一次设置后TL不可变，则继承可以提高效率，但可以考虑设置TL的方法。现在，它将根据其调用方是否设置了相同的TL引发非法状态异常，从而严重损害代码的可组合性。

为了解决这些问题，我们正在探索一种在性能、占用空间、结构和正确性方面更好的替代方法，我们尝试性地调用范围变量。与TLs一样，SVs引入了一些隐式上下文，但与TLs不同，它们是针对代码块的span而构造的，而不是针对线程的整个生命周期。SV也是不可变的，尽管它们的值可以被嵌套的作用域遮蔽。

这是使用当前EA原型中的`java.lang.Scoped` API的示例：

```java
static final Scoped<String> sv = Scoped.forType(String.class);

void foo() {
    try (var __ = sv.bind("A")) {
    bar();
    baz();
    bar();
  }
}

void bar() {
  System.out.println(sv.get());
}

void baz() {
  try (var __ = sv.bind("B")) {
    bar();
  }
}
```

baz不会更改sv的绑定，而是在嵌套作用域中引入了新的绑定，从而隐藏了其封闭的绑定。因此foo将输出：

```
A
B
A
```

因为SV绑定的生命周期是明确定义的，所以我们不需要依赖GC进行清理，因此我们不需要弱引用来减慢我们的速度。

那继承呢？由于SV是不可变的，并且结构化并发还为我们提供了语法限制的线程生命周期，因此SV继承就像手套一样适合结构化并发：

```java
try (var context = Foo.openContext()) { // some temporary context that can be closed
  try (var __ = contextSV.bind(context);
       var executor = Executors.newUnboundedExecutor(myThreadFactory)) {
    executor.submit(() -> { ... });
    executor.submit(() -> { ... });
  }
}
```

提交的任务会自动继承contextSV的上下文值，并且由于`UnboundedExecutor`范围被上下文的生命周期范围所包围，因此可以确定任务从contextSV获得的上下文尚未关闭。

其他类型的结构化构造（即其计算仅限于语法元素的构造）也可以提供自动SV继承。例如：

```java
try (var __ = sv.bind(value)) {
    Set.of("a", "b", "c").stream().parallel()
       .forEach(s -> System.out.println(s + ": " + sv.get()));
}
```

由于流的`forEach`操作也完全受限于SV的绑定范围，即使`forEach`可能在不同线程中的不同流元素上执行其主体，值也可以继承。

范围变量仍处于设计阶段的早期，并且与我们可能会引入try-with-resources的更一般的更改相关联（请参阅[此处](https://bugs.openjdk.java.net/browse/JDK-8243098)以了解一些想法）。即使我们决定使用SV，它们也可能会错过第一个Preview和GA。

# 处理器本地变量

线程本地变量的另一种用法不是将数据与线程上下文关联，而是“标记”一些写量大、易变的数据结构，以避免争用(例如LongAdder，它不使用`ThreadLocal`类，但依赖于类似的思想)。当线程数不比内核数大很多时，这是有道理的，但是可能有数百万个线程，这纯粹是开销。我们正在探索一种具有类似CAS语义的“处理器本地”结构，如果具有适当的OS支持（例如Linux的可重启序列），它比无竞争的CAS还要快。

# 有关中断和取消的更多信息

线程支持一种协作中断机制，该机制由方法**interrupt**，**interrupted**，**isInterrupted**和**InterruptedException**组成。这是一种相当复杂的机制：某些线程在另一个线程上调用中断，从而设置目标线程的中断状态。目标线程轮询其中断状态，可能会从阻塞方法中抛出**InterruptedException**，但也会清除该状态，这有两个原因。首先，线程可能是池中的共享资源。当前任务可以被中断，但是调度程序可能想要重用线程来运行其他任务，因此必须重置中断状态。对于虚拟线程，这是不必要的，因为它们足够轻巧，不会被重复用于其他任务。但是还有另一个原因：线程可能会观察到它已被中断，并且在清理过程中可能希望调用阻塞方法。如果状态未清除，则阻塞方法将立即引发**InterruptedException**。尽管此机制确实可以满足实际需求，但它容易出错，因此我们希望对其进行重新讨论。我们已经试验了一些原型，但是目前还没有任何具体方案。

# 强制抢占

尽管已经有了关于[调度](https://cr.openjdk.java.net/~rpressler/loom/loom/sol1_part1.html#scheduling)的说法，但在某些特殊情况下，强行抢占占用CPU的线程可能会很有用。例如，代表多个客户端应用程序执行复杂数据查询的批处理服务可以接收客户端任务，并在各自的虚拟线程中运行它们。如果此类任务占用过多的CPU，则该服务可能要强行抢占它，并在该服务负载较轻时再次安排它。为此，我们计划让VM支持尝试在任何安全点强制抢占执行的操作。该功能如何向调度程序公开是待定的，并且可能不会出现在第一个预览版中。
