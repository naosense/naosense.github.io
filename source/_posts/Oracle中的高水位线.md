---
title: Oracle中的高水位线
date: 2016-03-25 09:37:21
categories:
tags: [高水位线, oracle, 数据库]
---
高水位线(High Water Mark, HWM)类似于一个指针，用来标识分配给段(segment)的块(block)状态。块是Oracle中数据分配和操作的最小单位，段是类似于表、索引这样的数据库实体。块有下面几种状态：
- 在HWM之上，块是未格式化和未使用的(unformated and unused)
- 在HWM之下，块又有下面几种状态：
 - 分配的(allocated)，但是还未格式化
 - 格式化并且存有数据
 - 格式化但是没有数据，delete操作会造成这种状态

另有一个低水位线的概念(Low HWM)，处于Low HWM之下的块都是格式化的，处于Low HWM和HWM之间有可能格式化也可能未格式化。
示意图如下，
```
-- =============================================================
-- <-formated-->Low HWM<----allocated----->hwm<-----empty---->total
-- ================^========================^===================^
```
HWM有如下特点：

- 一般情况下只升不降，只有在truncate、move、shrink等操作才会降低，delete不会降低，delete后留下的空间，以后insert可以使用。
- 执行全表扫描时，数据库扫描Low HWM以下所有的块，不管有没有数据，读取两个水位线之间的块时则要小心一点，因为这中间的块并不一定都是格式化的。如果频繁的删除插入操作，会在HWM下的块中留下大量碎片，影响性能。
- 当insert和update的时候，数据库在Low HWM和HWM之间或者Low HWM之下的空余空间进行写入。


可是为什么要设置一个HWM呢？既然有了一个位图块记录块的状态，为什么要设置一个水位线，全表扫描时还要扫描下面的所有块，而不是那些有数据的？这不是出力不讨好吗，百度了半天，没找到满意的答案，基本上大家都是说“它是这样的”，而没有说“它为什么是这样的”，知道的告诉一声。

下面是检测表水位线的一个小程序：
```sql
PROCEDURE P_TABLE_HWM_ANALYSE(TABLE_NAME IN VARCHAR2) IS
    -- 表占用空间高水位检测
    LVC_TABLE_TMP        VARCHAR2(50);
    LVC_MB               NUMBER; -- 表的大小MB
    LVC_TOTAL            NUMBER; -- 总的block数
    LVC_BLOCKS           NUMBER; -- 水位线，即hwm
    LVC_EMPTY_BLOCKS     NUMBER; -- 空余block
    LVC_USED             NUMBER; -- 使用的block
    LVC_USED_PERCENT     NUMBER; -- 使用百分比，LVC_USED/LVC_TOTAL
    LVC_HWM_PERCENT      NUMBER; -- 水位线百分比，LVC_BLOCKS/LVC_TOTAL
    LVC_USED_PERCENT_POS NUMBER;
    LVC_HWM_PERCENT_POS  NUMBER;
  BEGIN
    LVC_TABLE_TMP := UPPER(TABLE_NAME);

    EXECUTE IMMEDIATE 'ANALYZE TABLE ' || LVC_TABLE_TMP ||
                      ' ESTIMATE STATISTICS';

    SELECT ROUND(SUM(DECODE(BYTES, NULL, 0, BYTES)) / 1024 / 1024, 1),
           SUM(DECODE(BLOCKS, NULL, 0, BLOCKS))
      INTO LVC_MB, LVC_TOTAL
      FROM USER_SEGMENTS
     WHERE SEGMENT_NAME = LVC_TABLE_TMP
     GROUP BY SEGMENT_NAME;

    SELECT DECODE(BLOCKS, NULL, 0, BLOCKS),
           DECODE(EMPTY_BLOCKS, NULL, 0, EMPTY_BLOCKS)
      INTO LVC_BLOCKS, LVC_EMPTY_BLOCKS
      FROM USER_TABLES
     WHERE TABLE_NAME = LVC_TABLE_TMP;

    EXECUTE IMMEDIATE 'SELECT COUNT(DISTINCT DBMS_ROWID.ROWID_BLOCK_NUMBER(ROWID)
                        || DBMS_ROWID.ROWID_RELATIVE_FNO(ROWID)) FROM ' ||
                      LVC_TABLE_TMP
      INTO LVC_USED;

    IF LVC_TOTAL = 0 THEN
      LVC_USED_PERCENT := 0;
      LVC_HWM_PERCENT  := 0;
    ELSE
      LVC_USED_PERCENT := ROUND(LVC_USED / LVC_TOTAL * 100);
      LVC_HWM_PERCENT  := ROUND(LVC_BLOCKS / LVC_TOTAL * 100);
    END IF;

    IF LVC_USED_PERCENT < 6 THEN
      LVC_USED_PERCENT_POS := 3;
    ELSE
      LVC_USED_PERCENT_POS := ROUND(LVC_USED_PERCENT / 2);
    END IF;

    IF LVC_HWM_PERCENT < 6 THEN
      LVC_HWM_PERCENT_POS := 3;
    ELSE
      LVC_HWM_PERCENT_POS := ROUND(LVC_HWM_PERCENT / 2);
    END IF;
    DBMS_OUTPUT.PUT_LINE(RPAD(LVC_TABLE_TMP || ': ' || LVC_MB || 'MB', 50) ||
                         LPAD('U: Used, H: HWM, T: Total', 52));

		DBMS_OUTPUT.PUT_LINE(LPAD('=', 102, '='));
    DBMS_OUTPUT.PUT_LINE(LPAD(LVC_USED_PERCENT || '%',
                              LVC_USED_PERCENT_POS));
    DBMS_OUTPUT.PUT_LINE('|' || LPAD('|U', LVC_USED_PERCENT + 2, '-'));
    DBMS_OUTPUT.PUT_LINE(LPAD(LVC_HWM_PERCENT || '%', LVC_HWM_PERCENT_POS));
    DBMS_OUTPUT.PUT_LINE('|' || LPAD('|H', LVC_HWM_PERCENT + 2, '-'));
		DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE(LPAD('T', 103, '='));

  EXCEPTION
    WHEN OTHERS THEN
      DBMS_OUTPUT.PUT_LINE(LVC_TABLE_TMP || ', ' || SQLERRM);

  END P_TABLE_HWM_ANALYSE;
```

测试一下，
```
DM2_LDCX_SY: 10MB                                                            U: Used, H: HWM, T: Total
======================================================================================================
                                         88%
|----------------------------------------------------------------------------------------|U
                                              98%
|--------------------------------------------------------------------------------------------------|H

======================================================================================================T
```
