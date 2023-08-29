---
title: 万锁之母AbstractQueuedSynchronizer
date: 2019-03-12 15:55:02
categories:
tags: [并发, 分布式, Java]
---
翻看[Java“锁”记](https://naosense.github.io/2019/03/07/Java%E2%80%9C%E9%94%81%E2%80%9D%E8%AE%B0/)中提到的各种“锁”，其内部同步实现大多数都和一个类`AbstractQueuedSynchronizer`相关，这个类称得上“万锁之母”，所以今天就来扒一扒这个类。

<!--more-->

## 整体脉络
为了避免一头扎进去纠缠于各种细节出不来，可以先从宏观上来看一下这个类。首先大家思考一个问题：什么是同步器？假如把线程比作车辆，同步器的角色和警察叔叔差不多，警察的做的事无非是在合适的时机指挥车辆走和停，同步器呢，也是在选择合适的时间调度线程阻塞和执行。

对于车辆来说，什么时候走什么时候停呢，警察叔叔给你招手的时候啊，来来来小伙子，否则就老老实实排队，等警察叔叔给你招手；对于线程来讲也可以采用这种策略，获得许可可以执行，否则排队阻塞，等同步器给与你许可。如果前方交通比较疏松，警察可能一次会叫好几辆车一起走，如果比较拥堵，则会一辆一辆的来；同步器呢同样如此，它有两种模式：共享和独占，前者允许多个线程一起运行，后者只允许单一线程运行。

如果用伪代码表示上面的逻辑可能是这样子的：
```java
// 获得许可
while (不允许获得许可) {
    线程排队
    停止执行
}
从队伍里出来继续执行

// 释放许可
if (允许释放许可) {
    释放许可
    叫醒排队的线程
}
```
经过上面的分析大致可以提炼出同步器要解决这么几点：
1. 许可怎么获取和释放
1. 线程采用什么方法停止和继续执行
3. 对于不能立马获得许可的线程得有排队机制

## 源码分析
说是源码分析其实是自己在学习`AbstractQueuedSynchronizer`源码的一些学习笔记，并不是完整的源码分析。相信想了解`AbstractQueuedSynchronizer`运行机制的人多多少少都看过它的代码了，甚至看了一遍都不止，其实大部分代码一般人都能看懂，就是有那么几处难懂的代码，犹如芒刺在背不拔不快。本文就是为了这个目的而写的，并不是要面面俱到而是重点突破，给有心人一点启发。为了符合上下文的语义，下面描述的时候可能节点和线程交替使用，也会把阻塞停止，唤醒叫醒混用，大家留意就是了。

`AbstractQueuedSynchronizer`整体是利用模板模式，通过维护一个`state`变量状态配合`tryAcquire`，`tryRelease`以及`tryAcquireShared`，`tryReleaseShared`间接的影响许可获取和释放。

同步器使用CLH队列来维护排队的线程，CLH队列说白了就是一个单向链表，特性是后一个节点的状态是由前一个节点的状态决定的，每个节点都有一个`pred`指针指向前一个节点，`AbstractQueuedSynchronizer`在原生的CLH队列基础上进行了优化，加入了一个`next`指针，指向后继节点，用于提高寻找后继节点的性能，这就形成了一个双向链表。由于没有更新两个`volatile`的变量的CAS方法，所以`next`变量为`null`的时候并不表明没有后继节点，因为有可能一个节点入列的时候更新完`pred`指针，还没来得及更新`next`指针。具体结构如下：

![CLH队列结构](https://wocanmei-hexo.nos-eastchina1.126.net/%E4%B8%87%E9%94%81%E4%B9%8B%E6%AF%8DAbstractQueuedSynchronizer/CLH.png)

`head`和`tail`分别指向队列的头和尾，`next`我这里画成了虚线，表明其不可靠性。

`AbstractQueuedSynchronizer`的核心就是如何维护CLH队列的状态，所以我们把重点放在这一块。它提供了两套获取许可和释放许可的方法：`acquire`，`release`和`acquireShared`，`releaseShared`，分别对应独占和共享模式。下面分别看看这两套方法的签名：
```java
// 独占模式模板方法
public final void acquire(int arg) {
    if (!tryAcquire(arg) &&
        acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
        selfInterrupt();
}

public final boolean release(int arg) {
    if (tryRelease(arg)) {
        Node h = head;
        if (h != null && h.waitStatus != 0)
            unparkSuccessor(h);
        return true;
    }
    return false;
}

// 共享模式模板方法
public final void acquireShared(int arg) {
    if (tryAcquireShared(arg) < 0)
        doAcquireShared(arg);
}

public final boolean releaseShared(int arg) {
    if (tryReleaseShared(arg)) {
        doReleaseShared();
        return true;
    }
    return false;
}
```
可以看到这两套方法是非常类似的，我们一个一个的看看，首先看看`acquire`方法：
```java
// acquire方法的逻辑粗看起来可能是先尝试获取下许可
// 如果成功，直接跳出，不用排队了；
// 如果不成功就添加一个独占节点到队列中排队，如果
// 有中断响应中断，细节一个方法一个方法的进入看看
public final void acquire(int arg) {
    if (!tryAcquire(arg) &&
        acquireQueued(addWaiter(Node.EXCLUSIVE), arg))
        selfInterrupt();
}

// 尝试获取许可，成功返回true，这个方法没有实现
// 而是留给子类去实现，因为不同的锁获取和释放
// 许可的语义是不同的无法一概而论，所以交由
// 具体的子类去实现，这是典型的模板模式
// 之所以没有用抽象方法，是因为同步器
// 允许只实现独占和共享的一种，如果是
// 抽象方法，则需要实现两套模式的方法
protected boolean tryAcquire(int arg) {
    throw new UnsupportedOperationException();
}

// 从名字上也可以看出这个方法就是往队伍里添加节点进行排队
private Node addWaiter(Node mode) {
    // 以当前线程建立一个新的节点，准备插到队伍里
    Node node = new Node(Thread.currentThread(), mode);
    // Try the fast path of enq; backup to full enq on failure
    // 这句是原生英文注释，大意是先尝试快速的路径入队，如果失败
    // 再用完整的入队方法，为什么这里是快呢？先别急，先往下看
    Node pred = tail;
    // pred != null 说明队伍里已有排队者
    if (pred != null) {
        node.prev = pred;
        // 使用CAS操作将当前节点插到队伍里，注意这个时候可能
        // 会有多个线程在同时往里插队，但是CAS操作能确保同一
        // 时间只有一个线程会成功
        if (compareAndSetTail(pred, node)) {
            pred.next = node;
            return node;
        }
    }
    enq(node);
    return node;
}

// 这就是所谓的完整的入队方法
private Node enq(final Node node) {
    for (;;) {
        Node t = tail;
        // 也就是队列还没有初始化呢，将head和
        // tail都初始化为一个哑节点
        if (t == null) { // Must initialize
            if (compareAndSetHead(new Node()))
                tail = head;
        } else {
            // 看这段代码是不是很眼熟了呢，对
            // 这块和快速入队方法基本一样，对比快速和完整
            // 两种入队方法，快速的没有初始化判断，
            // 少了循环，不会重试，相对来说会“快”点
            node.prev = t;
            if (compareAndSetTail(t, node)) {
                t.next = node;
                return t;
            }
        }
    }
}

// 这个方法的大意是如果获得了许可，赶紧出队执行，否则告诉你的
// 前继节点轮到你时叫你，然后老老实实排队等待
final boolean acquireQueued(final Node node, int arg) {
    boolean failed = true;
    try {
        boolean interrupted = false;
        for (;;) {
            // 获得node的前继节点
            final Node p = node.predecessor();
            // 如果前继节点是头而且尝试获取许可成功
            // 也就是轮到node出列执行了，即警察叔叔
            // 给你招手了
            if (p == head && tryAcquire(arg)) {
                setHead(node);
                p.next = null; // help GC
                failed = false;
                return interrupted;
            }
            // 这里是判断是否需要阻塞，需要的话就要调用
            // park方法将线程歇一会，等unpark叫醒线程
            // 的时候会检查中断状态，如果有中断就响应
            // 中断
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                interrupted = true;
        }
    } finally {
        // 如果tryAcquire抛出异常
        if (failed)
            cancelAcquire(node);
    }
}

// 这段代码的大意是节点node给前面的节点pred说哥们我先睡会，到站叫我，pred
// 说好（设置为SIGNAL状态），到站之后叫你，你放心睡吧
private static boolean shouldParkAfterFailedAcquire(Node pred, Node node) {
    int ws = pred.waitStatus;
    // 如果前继节点的状态是SIGNAL，表明node已经告诉pred到站叫他，
    // 而且pred也已经答应了，所以node可以放心的去睡了
    if (ws == Node.SIGNAL)
        return true;
    if (ws > 0) {
        // 这里是删除取消的节点，因为只有CANCEL的节点是大于0
        do {
            node.prev = pred = pred.prev;
        } while (pred.waitStatus > 0);
        pred.next = node;
    } else {
        // node告诉pred到站叫它
        compareAndSetWaitStatus(pred, ws, Node.SIGNAL);
    }
    return false;
}

// 这个方法很简单，没啥好说的，就是去睡觉，醒来
// 之后看看手机有没有人找你（中断）
private final boolean parkAndCheckInterrupt() {
    LockSupport.park(this);
    return Thread.interrupted();
}
```

`acquire`分析完了，再看看`release`
```java
// 如果释放许可成功，并且后面还有节点，叫醒它
// 返回
public final boolean release(int arg) {
    if (tryRelease(arg)) {
        Node h = head;
        // 如果后面还有节点
        // waitStatus会被设置成SIGNAL，忘记的话可以再
        // 看看前面的shouldParkAfterFailedAcquire方法
        if (h != null && h.waitStatus != 0)
            unparkSuccessor(h);
        return true;
    }
    return false;
}

// 叫醒后面的哥们一次
private void unparkSuccessor(Node node) {
    int ws = node.waitStatus;
    // 如果ws小于0，也就是没有取消，将ws置位0
    // 也就是打算叫醒后面的节点，同时把提醒
    // 状态复位，免得叫醒多次
    if (ws < 0)
        compareAndSetWaitStatus(node, ws, 0);

    Node s = node.next;
    // 如果后面可能没节点了或者节点是取消的
    // 就从后往前找，如果能找到紧随node之后
    // 并且没有取消的节点就叫醒它。这里就是
    // 利用next的优化了，即如果next不为空
    // 且没有取消那么直接叫醒next，如果
    // next为空，不能认定后面就没有节点了
    // 因为next是不可靠的，要利用可靠的pred从后
    // 往前找
    if (s == null || s.waitStatus > 0) {
        s = null;
        for (Node t = tail; t != null && t != node; t = t.prev)
            if (t.waitStatus <= 0)
                s = t;
    }
    if (s != null)
        LockSupport.unpark(s.thread);
}
```
独占模式的获取和释放代码就分析完了，再来看看共享模式的。
```java
public final void acquireShared(int arg) {
    if (tryAcquireShared(arg) < 0)
        doAcquireShared(arg);
}

// 返回值小于0表示获取失败
// 等于0表示获取许可成功但是后面节点无法再获取了
// 大于0表示获取许可成功并且后面节点还可以再获取
protected int tryAcquireShared(int arg) {
    throw new UnsupportedOperationException();
}

// 粗看doAcquireShared和acquireQueued非常相似，
// 主要是两点不同，一是一个添加的是独占节点，
// 一个添加的是共享节点，另一点不同是
// 一个是setHead，一个是setHeadAndPropagate
private void doAcquireShared(int arg) {
    final Node node = addWaiter(Node.SHARED);
    boolean failed = true;
    try {
        boolean interrupted = false;
        for (;;) {
            final Node p = node.predecessor();
            if (p == head) {
                int r = tryAcquireShared(arg);
                if (r >= 0) {
                    setHeadAndPropagate(node, r);
                    p.next = null; // help GC
                    if (interrupted)
                        selfInterrupt();
                    failed = false;
                    return;
                }
            }
            if (shouldParkAfterFailedAcquire(p, node) &&
                parkAndCheckInterrupt())
                interrupted = true;
        }
    } finally {
        if (failed)
            cancelAcquire(node);
    }
}

// 可以看到setHeadAndPropagate不光像独占模式那样修改了队列的头，
// 还会在某些条件下调用一个doReleaseShared方法
private void setHeadAndPropagate(Node node, int propagate) {
    Node h = head; // Record old head for check below
    setHead(node);

    // 后续节点还有获取许可的机会或者节点没有取消
    if (propagate > 0 || h == null || h.waitStatus < 0 ||
        (h = head) == null || h.waitStatus < 0) {
        Node s = node.next;
        // 不知道s是什么类型或者s是共享节点
        if (s == null || s.isShared())
            doReleaseShared();
    }
}

// 在并发的条件下叫醒队列头部的线程
private void doReleaseShared() {
    for (;;) {
        Node h = head;
        if (h != null && h != tail) {
            // 这部分代码和独占模式的release方法几乎一样
            // 也是把队列头的线程叫醒继续执行，但要注意
            // 一个重要区别是这里使用的是CAS操作，上面
            // 独占不是，这是为什么呢？还记得独占和共享
            // 的定义吗？对于共享模式多个线程同时执行
            // 同时也有可能多个线程同时释放，所以必须
            // 使用CAS操作保证线程安全
            int ws = h.waitStatus;
            if (ws == Node.SIGNAL) {
                if (!compareAndSetWaitStatus(h, Node.SIGNAL, 0))
                    continue;            // loop to recheck cases
                unparkSuccessor(h);
            }
            // 这个分支啥时候会满足呢？根据上面的分析在入队的时候
            // 会调用shouldParkAfterFailedAcquire将前继节点的状态
            // 修改为SIGNAL，这里为0应该发生在头节点没有后继节点
            // 或者后继节点调用shouldParkAfterFailedAcquire
            // 还没返回的时候，再加上这个条件：
            // !compareAndSetWaitStatus(h, 0, Node.PROPAGATE)
            // 那么就剩下了一种情况：头结点的后继节点调用
            // shouldParkAfterFailedAcquire还没把头节点
            // 的状态修改成SIGNAL的时候。如果没有这个分支
            // 只能等待下一次的doReleaseShared的调用才能
            // 将头部的线程叫醒了
            else if (ws == 0 &&
                     !compareAndSetWaitStatus(h, 0, Node.PROPAGATE))
                continue;                // loop on failed CAS
        }
        // 这句意思是头没变就跳出，那头啥时候变呢，就是出队的时候
        // 也就是有线程已经出队，有责任叫醒新的头节点线程
        if (h == head)                   // loop if head changed
            break;
    }
}

// 可以看到释放许可的主逻辑就是doReleaseShared
// 上文已经分析过在此不再赘述
public final boolean releaseShared(int arg) {
    if (tryReleaseShared(arg)) {
        doReleaseShared();
        return true;
    }
    return false;
}
```
## 运行图景
经过上面的源码分析，估计大部分人心里有点数了，可能还形不成清晰的运行图景或者说直觉性的认识，那么接下来说下我自己的一点理解。

整个的图景是这样子的：对于独占模式，因为只有一个线程能获取许可，进而也只有一个线程释放许可，只会叫醒队伍头部的一个线程，这样整个队列是**串行出列，并行入列**，有点像排队坐公交，虽然队伍后面挤作一团，队伍前面还是有序的，一个一个的上车；对于共享模式而言，由于允许多个线程一起运行，也就是多个线程获得许可，同样也会有多个线程释放许可，这就需要叫醒队伍里多个线程，整个队列的样子是**并行出列，并行入列**。

忽略不必要的细节，来看看独占和共享模式下主逻辑的函数调用栈：

![函数主逻辑调用栈](https://wocanmei-hexo.nos-eastchina1.126.net/%E4%B8%87%E9%94%81%E4%B9%8B%E6%AF%8DAbstractQueuedSynchronizer/function_stack.png)

上图左边是独占模式的调用栈，右边是共享模式的调用栈。可以清晰看到为啥共享模式的可以唤醒多个节点，是因为它的调用栈形成了一个环，这样它就不会不停地叫醒后面的共享节点，就像一个连锁反应，并且获取许可和释放许可都会启动这个连锁反应；而独占模式没有形成环，叫醒一个节点就返回了，并且由于共享模式下获取和释放许可都会调用doReleaseShared，二者会形成竞争，这也是doReleaseShared内部使用CAS操作的一个原因。

总结一下，AQS其实就是一个由状态变量和CLH虚拟队列组成的一个基础并发组件，它维护了一套线程阻塞、排队、唤醒的机制。它可以工作在共享和非共享两种模式下，共享模式下允许多个线程一起运行，非共享模式只允许一个线程运行。

参考资料：
- JAVA并发编程实战
- Doug Lea, The java.util.concurrent Synchronizer Framework
