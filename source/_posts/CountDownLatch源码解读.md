---
title: CountDownLatch源码解读
date: 2023-08-05 10:43:12
categories:
tags: [Java, 并发, JUC]
---
之前写过一篇关于[AQS的源码分析](https://naosense.github.io/2019/03/12/%E4%B8%87%E9%94%81%E4%B9%8B%E6%AF%8DAbstractQueuedSynchronizer/)的文章，介绍了AQS是Java并发组件的基础，基础的介绍了，我们再看看它的应用，因此从这一篇开始我将依次介绍下AQS在Java各个并发组件如何应用的，先从`CountDownLatch`开始。

`CountDownLatch`，有时也叫闭锁，它的作用就像一个大门，初始是关着的，线程在“门外”等候通过，在某一时刻大门打开，线程一起通过，大门打开后一直会保持打开状态，不会再关闭。它用在什么场景呢？一个典型的场景是JVM的warmup，我们都知道JVM刚启动时，由于JIT还没介入，系统的响应是比较慢的，需要发送一些请求让JVM快速“热”起来，即所谓的warmup。这个过程需要确保warmup的请求处理完，才能去接线上的正常请求，这个场景就可以用`CountDownLatch`来实现。也就是`CountDownLatch`源码中抽象出的代码示例，

```java
 class Driver { // ...
   void main() throws InterruptedException {
     CountDownLatch startSignal = new CountDownLatch(1);
     CountDownLatch doneSignal = new CountDownLatch(N);

     for (int i = 0; i < N; ++i) // create and start threads
       new Thread(new Worker(startSignal, doneSignal)).start();

     doSomethingElse();            // don't let run yet
     startSignal.countDown();      // let all threads proceed
     doSomethingElse();
     doneSignal.await();           // wait for all to finish
   }
 }

 class Worker implements Runnable {
   private final CountDownLatch startSignal;
   private final CountDownLatch doneSignal;
   Worker(CountDownLatch startSignal, CountDownLatch doneSignal) {
     this.startSignal = startSignal;
     this.doneSignal = doneSignal;
   }
   public void run() {
     try {
       startSignal.await();
       doWork();
       doneSignal.countDown();
     } catch (InterruptedException ex) {} // return;
   }

   void doWork() { ... }
 }
 ```

可以看到上面的源码有两个闭锁，一个用来开始，一个用来结束，N个线程执行某种任务，比如发送warmup请求，`startSignal`可以确保这些请求一起发送，请求有的响应快，有的响应慢，`doneSignal`可以确保那些快的慢的一起结束。那么它是怎么做到的呢？我们一起看下源码。

```java
private static final class Sync extends AbstractQueuedSynchronizer {
    private static final long serialVersionUID = 4982264981922014374L;

    Sync(int count) {
        setState(count);
    }

    int getCount() {
        return getState();
    }

    protected int tryAcquireShared(int acquires) {
        return (getState() == 0) ? 1 : -1;
    }

    protected boolean tryReleaseShared(int releases) {
        // Decrement count; signal when transition to zero
        for (;;) {
            int c = getState();
            if (c == 0)
                return false;
            int nextc = c - 1;
            if (compareAndSetState(c, nextc))
                return nextc == 0;
        }
    }
}
```

`CountDownLatch`里有一个`Sync`类，看懂这个类，其实闭锁的原理就懂了。

还记得之前AQS那篇文章里说：

> AQS其实就是一个由状态变量和CLH虚拟队列组成的一个基础并发组件，它维护了一套线程阻塞、排队、唤醒的机制。它可以工作在共享和非共享两种模式下，共享模式下允许多个线程一起运行，非共享模式只允许一个线程运行。

`count`就是这个状态变量，我们知道，AQS的`tryAcquireShared`如果返回正数表示当前线程可以执行，并且后续其他线程也可以继续执行；如果返回0，表示当前线程可以执行，但是后续线程就好好的待着吧；如果返回负数，连当前线程也不能继续执行了，会进入休眠状态等待唤醒，`tryReleaseShared`方法如果成功会唤醒休眠中的线程，看起来闭环了。

**因为闭锁可能需要唤醒多个线程，因此AQS工作在共享模式下**。`Sync`重写了`tryAcquireShared`，使得`count`为0时，大门已开，畅通无阻，当前及后续线程继续执行，否则当前线程进入休眠，等待大门打开的那一刻，同时重写了`tryReleaseShared`使得下一个`count`为0时才能唤醒休眠的线程，也就是**唤醒只发生在`count`从1到0发生变化的那一刻，在这之前和在这之后都不会唤醒线程**，在这之前是`count`还没数到0，大门是关闭的，在这之后是`count`已经数到0了，大门已经开了，并且一直是打开的，不会关闭。

下面是`CountDownLatch`的两个核心方法`await`（一个不带超时，一个带超时）和`countDown`，前者用来拦住某些线程，后者倒计时控制闭锁打开，里面的核心就是上面介绍的两个方法，不再赘述。

```java
public void await() throws InterruptedException {
    sync.acquireSharedInterruptibly(1);
}

public boolean await(long timeout, TimeUnit unit)
    throws InterruptedException {
    return sync.tryAcquireSharedNanos(1, unit.toNanos(timeout));
}

public void countDown() {
    sync.releaseShared(1);
}
```
