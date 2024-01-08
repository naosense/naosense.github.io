---
title: Java多线程交替打印字符
date: 2019-06-05 10:13:15
categories:
tags: [java, 多线程]
---
> 有这样一个面试题：多线程打印AB字符

这玩意但凡有点Java基础的人，都会想到这是考察线程`wait`和`notify`，那么具体怎么做呢？如果长时间不写多线程程序，冷不丁的来一下，还真写不出。

先来复习下`wait`、`notify`的概念：

> wait: Causes the current thread to wait until either another thread invokes the notify() method or the notifyAll() method for this object, or a specified amount of time has elapsed.
> The current thread must own this object's monitor.

> notify: Wakes up a single thread that is waiting on this object's monitor. If any threads are waiting on this object, one of them is chosen to be awakened. The choice is arbitrary and occurs at the discretion of the implementation. A thread waits on an object's monitor by calling one of the wait methods.This method should only be called by a thread that is the owner of this object's monitor.

> notifyAll: Wakes up all threads that are waiting on this object's monitor.

根据Javadoc的注释，可以看出`wait`将会让出锁，进入`WAITING`状态，直到其他线程调用`notify(All)`，进入`AWAKENED`状态，在`wait`最终返回之前，需要获取锁。这意味着，`AWAKENED`的线程将和`BLOCKING`状态的线程一起竞争锁，如果竞争不过，继续待在`WAITING`状态。有几点需要注意：

- 无论是`wait`，还是`notify(All)`，都必须在持有锁的状态下调用
- `notify(All)`调用后不会释放锁，而是在离开`syntronized`区域后
- `AWAKENED`线程在竞争锁时没有任何优势，和`BLOCKING`线程优先级一样

`wait`的使用范式如下：

```java
synchronized (obj) {
   while (<condition does not hold>)
       obj.wait();
   ... // Perform action appropriate to condition
}
```

之所以使用循环条件判断，是为了防止线程**过早唤醒**，也就是发出`notify(All)`时条件谓词为真，到`wait`返回时，谓词不为真了。另外Javadoc指出，`WAITING`线程会有一定的几率自己醒来，而不是收到`notify(All)`的通知，虽然这极少发生。

回到最初的问题，可以启动两个线程，为他们分配一个名字`name`，分别为A和B，设置一个变量`ticket`保存着下一个可运行的线程名，只有`name == ticket`的线程才有权运行，这样只要改变`ticket`的值就可以控制线程的运行了，具体代码如下：

```java
public class Main {
    public static void main(String[] args) {
        new PrintChar('A').start();
        new PrintChar('B').start();
    }

    private static class PrintChar extends Thread {
        private static final Object lock = new Object();
        private static char running = 'A';
        private char name;

        public PrintChar(char name) {
            this.name = name;
        }

        @Override
        public void run() {
            for (int i = 0; i<10;i++) {
                synchronized (lock) {
                    while (name != running) {
                        try {
                            // System.out.print(" <" + name + " waiting> ");
                            lock.wait();
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }
                    System.out.print(name);
                    loop();
                    lock.notify();
                }
            }
        }

        private void loop() {
            if (running == 'B') {
                running = 'A';
            } else {
                running += 1;
            }
        }
    }
}
```

为了观察线程的运行等待状态，我们将注释放开，得到下面的结果，

```
A <A waiting> B <B waiting> A <A waiting> B <B waiting> A <A waiting> B ...
```

作为一个问题的延伸，考虑下面的问题：

> 多线程打印ABCDE

小伙伴们，你想到了吗？
