---
title: 一个初级阶段的五子棋ai
date: 2017-12-11 16:46:03
categories:
tags: [五子棋, minimax, alpha-beta]
---

## 一、前言

16年alpha狗接连击败李世石和柯洁后，自己就有个想法，能不能利用机器学习也鼓捣一个类似的五子棋ai？最初的想法是训练一个机器学习模型，喂给它一些棋局，让它自己能够学会落子规则，能够积累优势，最终取得胜利，而且随着下棋盘数的增加，自身的能力可以进一步的提高。但是传统的机器学习需要输入和响应，对于一局棋输入和响应又是什么呢，搜肠刮肚的把自己知道的的几种算法想了一遍，也在网上查了半天，或者模型太复杂，短时间没法掌握相关的知识，或者模型计算代价太高，动辄训练个几天，所谓远水解不了近渴，最好的能一个周末能整出一个初级的ai，能打败我就行，以后有时间功能可以慢慢加，这也是标题的由来。

<!-- more -->

## 二、Minimax算法

对于这种回合制的游戏，传统的方法就是利用minimax算法，那么什么是minimax算法呢，说白了，就是和人在脑子里模拟往下走几步一样，minimax算法也是模拟往下走棋，轮到自己时选自己最有利的，即max，轮到对方时选自己最不利的，即min，直到某一条件终止，然后选择一条对自己最有利的路径。由此可以看到，如果计算资源足够，计算机是可以找到一条可以使己方胜利的路径，但是事实上这是不可能的，以15X15的五子棋为例，大约有225!种可能的走法，想穷举出这么多种可能性，以目前的计算能力是达不到的，所以一般的做法是往下模拟走一定的步数，然后选择一条最优的。

## 三、评估函数

由算法描述，必须有一种方法对当前的局势进行衡量，通常的方法就是使用评估函数。评估函数可以根据当前局势给出一个分数，使局势成为可量化的数值。具体到五子棋就是统计棋局中的活三、活四等模式并给予一定的分数然后将总的分数相加，具体请参考代码。

## 四、优化

### 1、Alpha-beta剪枝

单纯的minimax算法复杂度是非常高的，从算法的描述，算法的复杂度应该是$O(b^d)$,d是往后走的步数，b是每一步棋可选的位置。以五子棋为例，模拟走5步大约是$225^5=576650390625$，显然这个数目还是太大，所以需要引进alpha-beta剪枝。这种算法就是用一个变量alpha保存着max一方可以得到的最优值，beta保存着min一方只允许max一方获得的最优值，当beta小于等于alpha时其他的情况就不用再看了，因为最优值的上限就是beta。

### 2、减少可选的落子位置

下过五子棋的可能都知道，如果落子的位置离己方和对方的棋子太远是没有意义的，因此我把这个距离限制为2，这样把原来b从225减少到了20~30，这个优化是很可观的。

### 3、历史启发

alpha-beta剪枝的效率是和下一步棋的顺序密切相关，如果最合适的那一步棋总是先计算那么算法的效率可以达到$O(b^\sqrt{d})$，这就相当于同样的时间原来只能往后推算5步，现在可以推算10步，而如果顺序不当，效率和没剪枝的minimax没什么两样。历史启发的原理就是记录那些发生剪枝次数最多的位置，以及得分的极值，赋予它们一定的值，以此来排序。

最终的核心代码如下，

```java
private int alphaBeta(Board board, int depth, int alpha, int beta, Player player) {
    if (board.status().isGameOver() || depth <= 0) {
        return board.evaluate(this, this.depth - depth);
    }

    Board.Pos bestPos = null;
    int v = (this == player) ? Integer.MIN_VALUE : Integer.MAX_VALUE;
    List<Board.Pos> childPos = sortChildPos(board);
    for (Board.Pos pos : childPos) {
        Board bd = new Board(board);
        bd.mark(pos, player);
        int w = alphaBeta(bd, depth - 1, alpha, beta, bd.getEnemy(player));
        if (this == player) {
            if (v < w) {
                v = w;
                bestPos = pos;
                if (depth == this.depth) {
                    this.best = new Move(v, pos);
                }
            }
            alpha = Integer.max(alpha, w);
        } else {
            if (v > w) {
                v = w;
                bestPos = pos;
            }
            beta = Integer.min(beta, w);
        }

        if (beta <= alpha) {
            this.history[pos.getRow()][pos.getCol()] += 2 << depth;
            break;
        }
    }
    if (bestPos != null) {
        this.history[bestPos.getRow()][bestPos.getCol()] += 2 << depth;
    }
    return v;
}
```

## 五、战力如何

首先是人机对战，当推算的步数达到4步时，我是没赢过，但是这并不能说明它的战力有多强，只能说明我的水平很臭，但是我的初步目标达到了；其次我让两个同等级的电脑对战50局，战绩如下，

| 等级（步数） | 先手赢 | 后手赢 | 平局 |
|--------|--------|--------|--------|
|    1    |    40    | 10 | 0 |
|    2    |    16    | 12 | 22 |
|    3    |    27    | 18 | 5 |

似乎印证了先手的胜率高一点。

## 六、下一步工作

1. 可以看到ai的战力是和评估函数密切相关的，获取一个比较好的评估函数是一个优化的方向。
2. 目前ai不能自我学习，如何让ai自我学习，并逐步变强是另一个方向，这也是重点方向。

如果想在我的代码上继续前进，请戳[这里](https://github.com/naosense/NewBe)，下图是一局电脑对战的动图。

![](https://wocanmei-hexo.nos-eastchina1.126.net/%E4%B8%80%E4%B8%AA%E5%88%9D%E7%BA%A7%E9%98%B6%E6%AE%B5%E7%9A%84%E4%BA%94%E5%AD%90%E6%A3%8Bai/gomoku.gif)

参考资料：

1. [Minimax](https://en.wikipedia.org/wiki/Minimax)
2. [Alpha-beta pruning](https://en.wikipedia.org/wiki/Alpha%E2%80%93beta_pruning)
3. [Killer_heuristic](https://en.wikipedia.org/wiki/Killer_heuristic)
