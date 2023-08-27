---
title: Semaphore源码解读
date: 2023-08-27 11:12:54
categories:
tags: [Java, 并发, JUC]
---
根据Java Doc的说法，`Semaphore`是一个控制访问某种资源并发量的组件。

> Semaphores are often used to restrict the number of threads than can access some (physical or logical) resource.

例如，下面是一个使用信号量来控制对`Item`池访问的类：

```java
class Pool {
    private static final int MAX_AVAILABLE = 100;
    private final Semaphore available = new Semaphore(MAX_AVAILABLE, true);

    public Object getItem() throws InterruptedException {
        available.acquire();
        return getNextAvailableItem();
    }

    public void putItem(Object x) {
        if (markAsUnused(x)) {
            available.release();
        }
    }      // Not a particularly efficient data structure; just for demo

    protected Object[] items = ... // whatever kindsof items being managed
    protected boolean[] used = new boolean[MAX_AVAILABLE];

    protected synchronized Object getNextAvailableItem() {
        for (int i = 0; i < MAX_AVAILABLE; ++i) {
            if (!used[i]) {
                used[i] = true;
                return items[i];
            }
        }
        return null; // not reached
    }

    protected synchronized boolean markAsUnused(Object item) {
        for (int i = 0; i < MAX_AVAILABLE; ++i) {
            if (item == items[i]) {
                if (used[i]) {
                    used[i] = false;
                    return true;
                } else {return false;}
            }
        }
        return false;
    }
}
```

这个例子，`available`是一个信号量，最大并发数是100，用这个信号量来控制调用`getItem`的并发数。我初看这个例子时，有个疑问，**那就是虽说信号量限制了并发访问数，但是`getNextAvailableItem`不是加锁了吗，最终不还是只有一个线程才能访问吗？** 后面想了想，这个例子的信号量用来控制的不是最终拥有访问权限的并发数，而是争夺这个权限的候选者的个数。就好比选举中，当选者和候选者的关系，在这两者之外，还有广大的普罗大众。

下面看看AQS在Semaphore是怎么使用的。

```java
abstract static class Sync extends AbstractQueuedSynchronizer {
    private static final long serialVersionUID = 1192457210091910933L;

    Sync(int permits) {
        setState(permits);
    }

    final int getPermits() {
        return getState();
    }

    final int nonfairTryAcquireShared(int acquires) {
        for (;;) {
            int available = getState();
            int remaining = available - acquires;
            if (remaining < 0 ||
                compareAndSetState(available, remaining))
                return remaining;
        }
    }

    protected final boolean tryReleaseShared(int releases) {
        for (;;) {
            int current = getState();
            int next = current + releases;
            if (next < current) // overflow
                throw new Error("Maximum permit count exceeded");
            if (compareAndSetState(current, next))
                return true;
        }
    }

    final void reducePermits(int reductions) {
        for (;;) {
            int current = getState();
            int next = current - reductions;
            if (next > current) // underflow
                throw new Error("Permit count underflow");
            if (compareAndSetState(current, next))
                return;
        }
    }

    final int drainPermits() {
        for (;;) {
            int current = getState();
            if (current == 0 || compareAndSetState(current, 0))
                return current;
        }
    }
}
```

这是`Semaphore`的核心代码。Sync继承了AQS，通过`state`状态变量维护最大并发许可数`permits`，获取许可就减去一定的许可，释放就增加一定的许可，最终通过`compareAndSetState`完成修改。

```java
/**
 * NonFair version
 */
static final class NonfairSync extends Sync {
    private static final long serialVersionUID = -2694183684443567898L;

    NonfairSync(int permits) {
        super(permits);
    }

    protected int tryAcquireShared(int acquires) {
        return nonfairTryAcquireShared(acquires);
    }
}

/**
 * Fair version
 */
static final class FairSync extends Sync {
    private static final long serialVersionUID = 2014338818796000944L;

    FairSync(int permits) {
        super(permits);
    }

    protected int tryAcquireShared(int acquires) {
        for (;;) {
            if (hasQueuedPredecessors())
                return -1;
            int available = getState();
            int remaining = available - acquires;
            if (remaining < 0 ||
                compareAndSetState(available, remaining))
                return remaining;
        }
    }
}
```

`Semaphore`可以设置成公平和非公平模式，二者唯一的差别就是公平模式会调用`hasQueuedPredecessors`判断前面是否还有等待的线程。如果前面还有排队的线程，直接返回失败，否则，和非公平逻辑一样。

Semaphore api看着不少，核心其实就两个`acquire`和`release`，都是围绕着Sync中的方法进行调用，就不赘述了。
