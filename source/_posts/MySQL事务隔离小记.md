---
title: MySQL事务隔离小记
date: 2019-03-31 13:28:34
categories:
tags: [事务, mysql]
---
大家都知道事务系统有四大特征：原子性、一致性、隔离性、持久性。隔离性是其中重要的一环，什么是隔离呢，顾名思义就是事务之间啥时候可见啥时候不可见，这就是MySQL的四个隔离级别：
- 未提交读（read uncommited）
- 提交读（read commited）
- 可重复读（repeatable read）
- 串行读（serializable）

<!--more-->
其实前两种从名字上就能理解什么意思，未提交读是事务没提交呢，别的事务就读到了，也就是可以读取事务的中间状态，即常说的脏读，这违反了事务的原子性和一致性；提交读呢，只有事务提交了，其他事务才可以读取，提交读解决了脏读问题却存在如下问题，比如A事务和B事务并行执行，假设A事务第一次读取了字段name是“小明”，这个时候B事务修改了name为“小红”，接下来A事务又读取了这个字段，发现“小明”变成了“小红”，“小明”去哪了，说好的隔离呢，这种问题被称为不可重复读，所以有时候提交读也称为不可重复读。

可重复读就是为解决不可重复读问题而出现的另一个隔离级别，也是MySQL的默认事务隔离级别。但是可重复读也不是完美无缺的，比如A事务和B事务同时执行，A先查找name字段为“小红”的记录发现没有，这时候B添加name为“小红”的记录，A又执行一次查询，发现有“小红”这条记录了，即所谓的幻行，A像产生了幻觉一样，这种问题被称为幻读。

串行读就是所有的事务串行化执行，看似完美解决了所有的问题，却付出了加锁同步的代价。

总结四种级别的问题矩阵：

| 隔离级别 | 脏读  | 不可重复读 | 幻度  | 加锁读 |
| :---:    | :---: | :---:      | :---: | :---:  |
| 未提交读 | 是    | 是         | 是    | 否     |
| 提交读   | 否    | 是         | 是    | 否     |
| 可重复读 | 否    | 否         | 是    | 否     |
| 串行读   | 否    | 否         | 否    | 是     |

综合来看，第一种隔离级别太低违反了原子性和一致性，最后一种串行读效率太低在实际项目中鲜见使用，第二第三种都有一个幻读的问题，接下来看看MySQL如何解决这个问题。

MySQL使用了一种称之为多版本并发控制（MVCC）的机制，通过在每行记录后面保存两个隐藏列，一个保存了行的创建时间，一个保存了行的删除时间，这里的“时间”实际上是版本号，说到版本号你可能会猜测这应该是一种类似于乐观锁的并发控制机制，没错，MySQL就是通过这两个列实现了一种乐观锁。每当开始一个事务，系统版本号自动递增，事务开始的版本号作为事务的版本号，下面分别看看各种操作下这两个版本号是如何控制并发的。

- 查询操作（select）时，读取创建时间小于等于事务版本且删除时间未定义或大于事务版本的那些行，翻译成人话就是只读取本次事务添加或之前就存在，并且至少截止到本次事务还没有删除的那些记录。
- 插入时（insert），行的创建时间设置为当前系统版本号。
- 删除时（delete），删除时间设为系统版本号。
- 修改时（update），将当前版本号作为新行的创建时间和旧行的删除时间，可见修改相当于删除和插入两个动作。

回过头看上面A第二次读取时如果按这种方式就不会出现幻行，因为A只会读取A之前就存在和A自身插入的行。但是MVCC如果工作在提交读的情况下，不就没法读取新提交的记录了，这与提交读的语义不是矛盾了？

带着这个疑问去看MySQL官方说明，原来MySQL有一个[consistent read](https://dev.mysql.com/doc/refman/5.7/en/glossary.html#glos_consistent_read)的概念，MySQL通过快照（snapshot）给每个事务返回结果，在可重复读的情况下快照由**本事务第一次**读取操作决定，也就是快照在第一次读取操作时就定了（本事务如果更新或删除其他事务提交的记录将会更新快照），而提交读**事务每次**读取都会更新快照。那么问题来了，快照是如何生成的呢？其实MySQL增加的两列不是上面所述的“创建时间”和“删除时间”，而是DB_TRX_ID，即最后一个对本行进行操作的事务版本号，另一个是DB_ROLL_PTR，称为滚动指针，它指向[undo log](https://dev.mysql.com/doc/refman/5.7/en/glossary.html#glos_undo_log)，undo log中包含了恢复到未修改前数据的必要信息，比方说insert了一条记录，undo log里就存上一条delete。MySQL就是利用这两个隐藏列和undo log来构建快照的，下面以一个简单的示例说明一下，假设当前隔离级别为可重复读：

![快照构建示例](https://wocanmei-hexo.nos-eastchina1.126.net/MySQL%E4%BA%8B%E5%8A%A1%E9%9A%94%E7%A6%BB%E5%B0%8F%E8%AE%B0/undo_log.png)

1. 事务1首先insert一条name为小红的记录，undo log里插入一条delete记录：事务：1：delete 小红，DB_TRX_ID为事务版本号：1，DB_ROLL_PTR指向undo log的第1条记录
2. 事务2执行select name=小红操作，由于DB_TRX_ID小于当前事务版本2，所以小红这条记录对事务2可见，最终小红这条记录返回
3. 在事务2执行过程中，事务3将小红更新成了小明，DB_TRX_ID需要更新成最新的事务版本号3，DB_ROLL_PTR指向undo log的第2条记录：事务：3：update 小明->小红
4. 事务2又执行select name=小红操作，由于DB_TRX_ID大于2，也就是在当前事务之后修改的，所以需要借助undo log回滚构建快照（不是真正的回滚），执行DB_ROLL_PTR指向的记录：update：事务：3：update 小明->小红，name由小明变为小红，执行select语句还是返回这条记录

当然MySQL真正的实现肯定比这复杂的多，这只是我根据看到的文档抽象的一个简化模型。

参考资料：
- 高性能MySQL
- [Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/5.7/en/innodb-consistent-read.html)
- [InnoDB Multi-Versioning](https://dev.mysql.com/doc/refman/5.7/en/innodb-multi-versioning.html)
