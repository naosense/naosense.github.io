---
title: 从乐高玩具到Parser Combinator
date: 2023-01-01 16:17:23
categories:
tags: [parser combinator, rust, scala]
---
## 什么是Parser Combinator

作为程序员，或多或少都会接触到解析字符串的任务， 比如从日志中解析出用户和id，这种工作可以用正则表达式轻松搞定，但是如果是解析json、xml这样复杂的结构，正则表达式就有点力不从心啦，这个时候有经验的程序员可能会想起Antlr、Yacc类似的解析器生成器，没错，这是一个可行的方案，这个方案需要你了解基本的词法、语法知识，编写一些晦涩的EBNF文件，不过好在除了这套方案，还有另一种方法，那就是今天要说的Parser Combinator。

<!--more-->
![lego](lego.png)

如果你去网上搜索它，上面的文章上来不是Monad、Functor，就是范畴论、幺半群这些玄而又玄的概念，以致于我虽然很早就听过Parser Combinator，但一直都只敢远观。直到最近看了Bodil[一篇文章](https://bodil.lol/parser-combinators/)，写的深入浅出。看完之后我才知道Parser Combinator原来是两种算子，一种叫解析器，另一种叫组合器，也叫组合子，原理也很直接，就像搭积木，由一些基本的构件搭出城堡的各个部分，再由各个部分搭出整个城堡，整个过程没啥玄学。原文中的程序是Rust编写的，考虑到Rust语言的受众规模，以及Rust的一些核心理念会平白增加编写Parser Combinator的难度，比如借用引用、生命周期，我打算用Scala重写一下，并按照Scala的习惯做下调整。

我一直认为最好的学习方法是*learn by doing*。因此建议大家在电脑上跟着敲一遍代码，哪怕只是粘贴一下看看运行效果，你绝对能找到和玩乐高类似的乐趣。

## 简化版xml解析器

我们的目标是编写一个简化版的xml解析器，因为完整的xml包含namespaces、schema等一大堆琐碎的概念，要实现一个完备的解析器用来作为入门还是过于复杂了，因此我们只实现xml的一个子集，下面是一段示例，

```xml
<parent-element>
  <single-element attribute="value" />
</parent-element>
```

可以看到，它的结构有两种：
- 一开一闭(open-close-element)：`<标识符></标识符>`
- 单元素(single-element)：`<标识符/>`

第一种通常会包含一些子元素，子元素通常又会包含孙元素，形成一种递归结构。标识符后面还会有一些空白符分割的可选属性对，比如上面的`attribute="value"`。合格的标识符由字母开头，后面可以使用字母数字或-。

### 解析器的类型

让我们首先想一下，什么是解析器？一个解析器就是给它一个字符串，然后它把你感兴趣的内容挑出来输出给你，在scala中就可以这么表示，

```scala
String => Try[(String, Output)]
```

`Try`有两个子类`Success`和`Failure`，正好可以用来表示解析成功与否，`(String, Output)`是一个二元组，前面的元素表示剩余未被解析的字符串，后面的`Output`表示最终的输出格式，由于这个格式不定，所以表示为一个泛型。

### 字符`a`解析器

先拿一个简单的练练手，来编写关于字符a的解析器。

```scala
def theLetterA(input: String): Try[(String, Unit)] = {
  input.toList match {
    case first :: rest if first == 'a' => Success((rest.mkString, ()))
    case _ => Failure(ParseError(input))
  }
}
case class ParseError(input: String) extends Throwable
case class Element(name: String, attributes: Vector[(String, String)], children: Vector[Element])
```

这段代码的逻辑是将`input`转成字符列表，如果第一个字符为a，则解析成功，否则失败。这里我们定义了自己的错误类`ParseError`以及最终的解析结果数据结构`Element`。你可能注意到输出的位置上写的是`Unit`，它的含义类似Java中的`void`，这表示我们并不关心解析器的输出，这种解析器的作用只是为了将输入的解析位置往前推进，这种类型的解析器下面还会看到。

### 字面量解析器

有了前面字符a的解析器基础，下面我们编写一个解析任意字符串字面量的解析器，

```scala
def literal(expected: String): Parser[Unit] = {
  (input: String) => {
    input.take(expected.length) match {
      case s if s == expected => Success((input.drop(expected.length), ()))
      case _ => Failure(ParseError(input))
    }
  }
}
```

注意看，这个函数属于高阶函数，它的返回值本身也是一个函数。基本逻辑是输入的开头部分如果和字面量`expected`匹配上就成功，否则失败。

下面编写这个解析器的测试用例，使用的测试框架是munit，

```scala
test("literal parser") {
  val parseJoe = literal("Hello Joe!")
  assertEquals(parseJoe.parse("Hello Joe!"), Success("", ()))
}
```

运行一下，测试通过。因为`literal`返回是一个函数，所以可以像函数那样调用它。作为一个小tip，如果你使用sbt，你可以使用`~testOnly YOUR-TEST_CASE`进行持续测试，源文件一发生改变，测试就会自动运行，可以提高测试的效率。

### 标识符解析器

还记得上面我们说过一个合法的标识符组成规则吗，对，首字符字母，后面是任意个字母数字或-。

```scala
def identifier(input: String): ParseResult[String] = {
  val matched = new StringBuilder()

  input.toList match {
    case first :: _ if first.isLetter => matched.append(first)
    case _ => return Failure(ParseError(input))
  }

  matched.append(input.drop(1).takeWhile(c => c.isLetterOrDigit || c == '-'))

  val nextIndex = matched.length;
  Success((input.drop(nextIndex), matched.toString()))
}
```

这里的逻辑是首先去检测第一个字符是不是合法，如果合法将它收集到`matched`中，并检测后续符合要求的字符并收集，否则直接失败退出。与之前不同的一点是，在返回值上`Output`的位置这次为`String`，这是因为标识符的名字通常是很重要的信息，我们需要将它保存下来。

同样，我们编写这个解析器的测试用例，

```scala
test("identifier parser") {
  assertEquals(identifier("i-am-an-identifier"), Success(("", "i-am-an-identifier")))
  assertEquals(identifier("not entirely an identifier"), Success((" entirely an identifier", "not")))
  assertEquals(identifier("!not at all an identifier"), Failure(ParseError("!not at all an identifier")))
}
```
这三个用例第一个很好理解，i-am-an-identifier一整个是一个合法的标识符，第二个因为空格不能包含在标识符中，所以解析到not后面的空格就终止了，第三个因为开头的叹号不属于合法的字符，因此返回失败。

### 组合组合子

现在解析字符串的解析器有了，解析标识符的解析器也有了，想要解析<identifier这样的字符串，还得有个将两个解析器组合起来的功能。

```scala
def pair[R1, R2](parser1: (String) => Try[(String, R1)], parser2: (String) => Try[(String, R2)]): String => Try[(String, (R1, R2))] = {
  (input: String) => {
    parser1(input) match {
      case Success((nextInput, result1)) => parser2(nextInput) match {
        case Success((finalInput, result2)) => Success((finalInput, (result1, result2)))
        case Failure(ex) => Failure(ex)
      }
      case Failure(ex) => Failure(ex)
    }
  }
}
```

这里的逻辑是`parser1`先去解析，如果失败直接退出，否则由`parser2`去解析剩余的输入`nextInput`，如果成功，将两个解析器的结果组成一个二元组输出，否则失败退出。这意味着，两个解析器的都得解析成功，整体才是成功，否则就失败了。

有了这个组合器我们就有了组合任意两个解析器的能力，有点搭积木的意思了哈。同样地，测试用例来一个。

```scala
test("pair combinator") {
  val tagOpener = pair(literal("<"), identifier _)
  assertEquals(tagOpener.parse("<my-first-element/>"), Success(("/>", ((), "my-first-element"))))
  assertEquals(tagOpener.parse("oops"), Failure(ParseError("oops")))
  assertEquals(tagOpener.parse("<!oops"), Failure(ParseError("!oops")))
}
```
注意第一个用例的`Output`类型为`((), String)`，`()`其实对我们没意义，我们只想要第二个解析器的结果，这就引申出来两个通用的组合子`left`和`right`，用于对结果进行修剪。

### 类型转换组合子

在认识`left`和`right`之前，我们先认识另一个通用的组合子`map`，map在很多编程语言中都有，作用大同小异，基本上就是将一个类型转换成另一个，有了它编写`left`和`right`就水到渠成了，因为使用`map`配合一个映射函数很容易就可以将二元组的其中一个元素挑出来。

```scala
def map[A, B](parser: (String) => Try[(String, A)], fn: A => B): (String) => Try[(String, B)] = {
  (input: String) => {
    parser(input) match {
      case Success((nextInput, result)) => Success((nextInput, fn(result)))
      case err@Failure(_) => err.asInstanceOf[Try[(String, B)]]
    }
  }
}
```

首先`parser`去解析`input`，如果成功，转换函数`fn`将输出转换为另一种类型，如果失败，将原始错误返回。

### 打扫屋子再请客

在继续前进之前，先让我们停下来看一看已经完成的代码，大量的`Try[(String, Output)]`，`String => Try[(String, Output)]`冗长的类型充斥期间，是时候对代码进行一波“打扫”了。首先，使用type alias对`Try[(String, Output)]`进行化简，

```scala
type ParseResult[Output] = Try[(String, Output)]
```

然后定义一个trait `Parser`，然后使用隐式转换机制将`String => Try[(String, Output)]`转换为`Parser`，

```scala
@FunctionalInterface
trait Parser[Output] {
  def parse(input: String): ParseResult[Output]
}

implicit def function2parser[Output](f1: String => ParseResult[Output]): Parser[Output] = {
  (input: String) => f1.apply(input)
}
```

然后使用`Parser`和`ParseResult`分别去替换`Try[(String, Output)]`和`String => Try[(String, Output)]`，比如`map`重写后的如下，

```scala
def map[A, B](parser: Parser[A], fn: A => B): Parser[B] = {
  (input: String) => {
    parser(input) match {
      case Success((nextInput, result)) => Success((nextInput, fn(result)))
      case err@Failure(_) => err.asInstanceOf[ParseResult[B]]
    }
  }
}
```

是不是比之前看起来比之前清爽多了。同样，重写下`pair`，

```scala
def pair[R1, R2](parser1: Parser[R1], parser2: Parser[R2]): String => ParseResult[(R1, R2)] = {
  (input: String) => {
    parser1(input) match {
      case Success((nextInput, result1)) => parser2(nextInput) match {
        case Success((finalInput, result2)) => Success((finalInput, (result1, result2)))
        case Failure(ex) => Failure(ex)
      }
      case Failure(ex) => Failure(ex)
    }
  }
}
```

同样的方式，将前面所有的代码进行下替换。

### 结果提取组合子

有了`pair`和`map`，`left`和`right`已经呼之欲出了。

```scala
def left[R1, R2](parser1: Parser[R1], parser2: Parser[R2]): Parser[R1] = {
  map(pair(parser1, parser2), { case (l, _) => l })
}

def right[R1, R2](parser1: Parser[R1], parser2: Parser[R2]): Parser[R2] = {
  map(pair(parser1, parser2), { case (_, r) => r })
}
```

逻辑很简单，`left`将二元组的第一个元素返回，`right`将二元组的第二个元素返回。

老样子，测试用例

```scala
test("right combinator") {
  val tagOpener = right(literal("<"), identifier _)
  assertEquals(tagOpener.parse("<my-first-element/>"), Success(("/>", "my-first-element")))
  assertEquals(tagOpener.parse("oops"), Failure(ParseError("oops")))
  assertEquals(tagOpener.parse("<!oops"), Failure(ParseError("!oops")))
}
```

这些用例和上面`pair`的用例极为相似，需要注意的只有第一个用例，观察和`pair`的第一个用例有哪些不同，对，类型由`((), String)`变成了`String`，这正是我们想要达成的效果。

### 表示重复的组合子

还记得我们最开始介绍xml格式的时候说过，xml包含一些可选的属性对，它们以空白字符分割。这里面有两个关键词：“一些”和“可选”，如何表示这种含义呢？为此我们抽象出两个组合子：“一次及以上”和“零次及以上”，想想看，正则表达式也有类似的设计。
我们先来看“一次及以上”

```scala
def oneOrMore[A](parser: Parser[A]): Parser[Vector[A]] = {
  (input: String) => {
    var result = Vector[A]()
    var remain = input
    parser.parse(remain) match {
      case Success((nextInput, firstItem)) => {
        remain = nextInput
        result :+= firstItem
        var break = false
        while (!break) {
          parser.parse(remain) match {
            case Success((nextInput, nextItem)) => {
              remain = nextInput
              result :+= nextItem
            }
            case Failure(exception) => break = true
          }
        }
        Success((remain, result))
      }
      case err@Failure(exception) => err.asInstanceOf[ParseResult[Vector[A]]]
    }
  }
}
```

这里的逻辑是`parser`解析**第一次**必须得成功，否则直接就失败了，因为是一次及以上嘛。之后，可以成功，也可以失败，都不重要。聪明的你肯定已经想到了“零次及以上”的写法，就是把第一段去掉呗。

```scala
def zeroOrMore[A](parser: Parser[A]): Parser[Vector[A]] = {
  (input: String) => {
    var result = Vector[A]()
    var remain = input

    var break = false
    while (!break) {
      parser.parse(remain) match {
        case Success((nextInput, nextItem)) =>
          remain = nextInput
          result :+= nextItem
        case Failure(_) => break = true
      }
    }
    Success((remain, result))
  }
}
```

不需赘述。

测试用例

```scala
test("one or more combinator") {
  val parser = oneOrMore(literal("ha"))
  assertEquals(parser.parse("hahaha"), Success(("", Vector((), (), ()))))
  assertEquals(parser.parse("ahah"), Failure(ParseError("ahah")))
  assertEquals(parser.parse(""), Failure(ParseError("")))
}

test("zero or more combinator") {
  val parser = zeroOrMore(literal("ha"))
  assertEquals(parser.parse("hahaha"), Success(("", Vector((), (), ()))))
  assertEquals(parser.parse("ahah"), Success(("ahah", Vector.empty)))
  assertEquals(parser.parse(""), Success("", Vector.empty))
}
```
注意比较这两个解析器的不同，后两个一样的用例，一个失败，一个成功。想想为什么？

### 谓词组合子

盘点一下，我们可以用`literal`解析<>这样的字面量，可以用`identifier`解析标识符，可以用`pair`组合任意两个解析器，可以使用`oneOrMore`或者`zeroOrMore`多次应用一个解析器，用这些去解析空白符分割的属性对时是否已经够了呢？注意这里是空白符，不单指空格，还包括制表符、换行符、回车符，还有一堆unicode字符也属于空白符。对，我们还缺少一个空白符解析器。

如果我们有“或”组合子，可以用它将一堆空格、制表符、换行符等连起来，但这个法子太笨了。我们是聪明人，我们肯定得用聪明的法子。聪明的办法是一种更通用的方法：抽象出一个谓词组合子，通过传入的谓词判断是否是空白符，在各种语言中，这种函数基本上是现成的。

```scala
def pred[A](parser: Parser[A], predicate: A => Boolean): Parser[A] = {
  (input: String) => {
    parser.parse(input) match {
      case Success((nextInput, value)) if predicate(value) => Success((nextInput, value))
      case _ => Failure(ParseError(input))
    }
  }
}
```

逻辑基本上就是上面所说的，只有当`parser`的结果符合`predicate`的要求时，才会返回成功，否则一律失败。

为了实现空白符解析器，还需要一个`anychar`，它的作用是返回任意一个字符，用来驱动解析位置往前走。

```scala
def anychar(input: String): ParseResult[Char] = {
  input.toList match {
    case first :: rest => Success((rest.mkString, first))
    case _ => Failure(ParseError(input))
  }
}
```

有了这两个，空白符就可以表示为符合`c => c.isWhitespace`的任意字符。

```scala
def whitespace(): Parser[Char] = {
  pred(anychar, c => c.isWhitespace)
}
```

老样子，编写下测试用例，验证下算子的逻辑

```scala
test("predicate combinator") {
  val parser = pred(anychar, (c: Char) => c == 'o')
  assertEquals(parser.parse("omg"), Success(("mg", 'o')))
}
```

有了`whitespace`，配合`oneOrMore`和`zeroOrMore`，就可以表示“一个及以上的空白符”和“零个及以上的空白符”。

```scala
def space1(): Parser[Vector[Char]] = {
  oneOrMore(whitespace())
}

def space0(): Parser[Vector[Char]] = {
  zeroOrMore(whitespace())
}
```

### 引用字符串

属性的值都是双引号包裹的字符串，因此我们还需要编写一个解析引用字符串的解析器，

```scala
def quotedString(): Parser[String] = {
  map(
    right(
      matchLiteral("\""),
      left(
        zeroOrMore(pred(anyChar, (c: Char) => c != '"')),
        matchLiteral("\"")
      )
    ),
    (chars: Vector[Char]) => chars.mkString
  )
}
```

这里的逻辑是，首先匹配开头的一个双引号，然后中间匹配除双引号之外的任何字符，最后再匹配结尾的一个双引号。使用`left`和`right`只将中间的值拿出来。
让我们快速写一个用例，来验证下正确性。

```scala
test("quoted string parser") {
  assertEquals(quotedString().parse("\"Hello Joe!\""), Success("", "Hello Joe!"))
}
```

不错，一切正常，胜利就在眼前！

### 属性对解析器

现在，关于属性解析已经万事俱备了，我们可以先写一个解析单个属性对的解析器，配合`zeroOrMore`再写出解析若干属性对的解析器。单个的如下，

```scala
def attributePair(): Parser[(String, String)] = {
  pair(identifier, right(literal("="), quotedString()))
}
```

逻辑直截了当，首先匹配一个标识符，再匹配一个＝，最后匹配属性值，也就是引用字符串。使用`zeroOrMore`将其组合起来就可以解析多个属性对了，同时不要忘了中间的空白符。

```scala
def attributes(): Parser[Vector[(String, String)]] = {
  zeroOrMore(right(space1(), attributePair()))
}
```

测试一下

```scala
test("attribute parser") {
  assertEquals(attributes().parse(" one=\"1\" two=\"2\""), Success("", Vector(("one", "1"), ("two", "2"))))
}
```

运行，一切正常，和谐完美！

### 一步之遥

随着“一块一块积木“的搭建，城堡最终的样子已经越来越清晰了。让我们稍微按捺一下激动的心情，回想一下上文说过的：xml的元素分两种，一种是一开一闭可以包含子元素`<div class="good">children</div>`，一种是单元素结构`<div class="good"/>`，它们有一个共同结构即`<div class="good"`部分，因此将这一部分提炼出来可能会大有用处。

```scala
def elementStart(): Parser[(String, Vector[(String, String)])] = {
  right(literal("<"), pair(identifier, attributes()))
}
```

首先去匹配`<`，然后匹配标识符和属性对，然后使用`right`将标识符和属性对的值拿出来放在`Vector[(String, String)]`。单元素的解析器如下，相比上面只需在后面匹配下`/>`就可以了。

```scala
def singleElement(): Parser[Element] = {
  map(
    left(elementStart(), matchLiteral("/>")),
    { case (name, attributes) =>
      Element(name, attributes, Vector())
    }
  )
}
```

类似地，open-element可以这么写，

```scala
def openElement(): Parser[Element] = {
  map(
    left(elementStart(), literal(">")),
    { case (name, attributes) => Element(name, attributes, Vector()) }
  )
}
```

注意它的返回值是我们一开始定义的`Element`，通过`map`算子将结果转成这个类型。 但是close-element咋写呢？这里的难点是开闭元素的名字要对应起来，在使用的时候将开元素的名字传进去。

```scala
def closeElement(expected: String): Parser[String] = {
  pred(
    right(
      literal("</"),
      left(identifier, literal(">"))
    ), name => name == expected
  )
}
```

开闭元素这一对可以表示为

```scala
def parentElement(): Parser[Element] = {
  pair(
    openElement(),
    left(zeroOrMore(element()), closeElement(**name**))
  )
}
```

但是如何把`openElement`的解析结果传给`closeElement`呢？这就要引入另一个通用组合子`flatMap`，为了更好的可读性将其放在`Parser`中，类似地，把`pred`、`map`也加一下，虽然它们只是外面的`pred`、`map`的简单映射，但是可以极大的改善代码可读性。

```scala
@FunctionalInterface
trait Parser[Output] {
  def parse(input: String): ParseResult[Output]

  def map[NewOutput](fn: Output => NewOutput): Parser[NewOutput] = {
    ParserCombinator.map(this, fn)
  }

  def pred(predicate: Output => Boolean): Parser[Output] = {
    ParserCombinator.pred(this, predicate)
  }

  def flatMap[NewOutput](fn: Output => Parser[NewOutput]): Parser[NewOutput] = {
    (input: String) => {
      this.parse(input) match {
        case Success((nextInput, result)) => fn(result).parse(nextInput)
        case err@Failure(_) => err.asInstanceOf[ParseResult[NewOutput]]
      }
    }
  }
}
```

`parentElement`使用新方法的样子

```scala
def parentElement(): Parser[Element] = {
  openElement().flatMap(el =>
    left(zeroOrMore(element()), closeElement(el.name))
      .map(children => el.copy(children = children))
  )
}
```

`openElement`将解析结果`el`返回，然会将`el.name`传给`closeElement`，这样只有open和close是一对才会成功。不过回顾xml的结构，我们还需要一个表示“或”的组合子，因为xml有两种元素结构。不过，这对已经身经百炼的你已经是易如反掌了。

```scala
def either[A](parser1: Parser[A], parser2: Parser[A]): Parser[A] = {
  (input: String) => {
    parser1.parse(input) match {
      case ok@Success(_) => ok
      case _ => parser2.parse(input)
    }
  }
}
```

`either`有两个解析器入参，如果`parser1`的结果成功，直接返回结果，如果失败，继续尝试`parser2`，直接将结果返回。这意味着，只要两个解析器只要有一个成功，那整体结果就是成功的。

### 最后一块积木

好吧，终于看到胜利的曙光了。让我们将最后一块积木放上去，然后好好欣赏下我们的作品吧！

```scala
def element(): Parser[Element] = {
  either(singleElement(), parentElement())
}
```

```scala
test("xml parser") {
  val doc =
    """<top label="Top">
      |    <semi-bottom label="Bottom"/>
      |    <middle>
      |        <bottom label="Another bottom"/>
      |    </middle>
      |</top>
      |""".stripMargin

  val parseDoc = Element(
    "top",
    Vector(("label", "Top")),
    Vector(
      Element("semi-bottom", Vector(("label", "Bottom")), Vector()),
      Element("middle", Vector(), Vector(Element("bottom", Vector(("label", "Another bottom")), Vector())))
    )
  )
  assertEquals(element().parse(doc), Success(("", parseDoc)))
}
```

运行下，竟然报错了，好在报错信息还是比较详细。

```
values are not the same
=> Diff (- obtained, + expected)
-Failure(
-  exception = ParseError(
-    input = """
-    <semi-bottom label="Bottom"/>
-    <middle>
-        <bottom label="Another bottom"/>
-    </middle>
-</top>
-"""
+Success(
+  value = Tuple2(
+    _1 = "",
+    _2 = Element(
+      name = "top",
+      attributes = Vector(
+        Tuple2(
+          _1 = "label",
+          _2 = "Top"
+        )
+      ),
+      children = Vector(
+        Element(
+          name = "semi-bottom",
+          attributes = Vector(
+            Tuple2(
+              _1 = "label",
+              _2 = "Bottom"
+            )
+          ),
+          children = Nil
+        ),
+        Element(
+          name = "middle",
+          attributes = Nil,
+          children = Vector(
+            Element(
+              name = "bottom",
+              attributes = Vector(
+                Tuple2(
+                  _1 = "label",
+                  _2 = "Another bottom"
+                )
+              ),
+              children = Nil
+            )
+          )
+        )
+      )
+    )
   )
```

仔细看下报错，可以看到解析器好像解析完`<top label="Top">`就停止了，这是咋回事呢？观察要解析的xml，在标签之间有许多换行和空格，而`element`并没有处理这一情况。

```xml
<top label="Top">
    <semi-bottom label="Bottom"/>
    <middle>
        <bottom label="Another bottom"/>
    </middle>
</top>
```

我们需要引入另一个组合子`wrap`，它会忽略周围的空白符。

```scala
def wrap[A](parser: Parser[A]): Parser[A] = {
  right(space0(), left(parser, space0()))
}
```

这应该就是xml解析器的完全体了。

```scala
def element(): Parser[Element] = {
  wrap(either(singleElement(), parentElement()))
}
```

重新运行下测试用例，通过，完美！真是好事多磨啊！

让我们简单的总结下，最开始通过`theLetterA`第一次认识了解析器，由此隐身出来解析字符串的`literal`，接下来又结识了解析标识符的`identifier`，然后通过`pair`将二者结合起来完成了对xml标识符的解析，接下来又引入了`map`、`oneOrMore`、`zeroOrMore`、`pred`等完成了对属性的解析，最后引入`either`处理单元素结构和包含子元素的开闭结构，整个过程是不是特别像搭积木？

### 下一步工作

如果想在实际项目中使用，我们这个toy解析器还是太naive了。如果大家想更深入的了解Parser Combinator，Scala可以看下[fastparse](https://github.com/com-lihaoyi/fastparse), Rust可以看下[nom](https://github.com/rust-bakery/nom)。

## Common Pattern

也许在一开始，你可能会疑问为啥要实现这些算子而不是那些算子，因为在上面的旅程中，你可能已经体会到到达终点的路不是一条，那为什么独独选这一条呢？很好的问题，事实上，上面的好多算子彼此有不少联系，一些更专有的算子可以用另一些更基础的算子重写，通过不停的分解，归并，你就会发现一些公共模式(Common Pattern)。

比如`pair`可以重写为，

```scala
def identifier(input: String): ParseResult[String] = {
pair(
  (anychar _).pred(c => c.isLetter),
  zeroOrMore((anychar _).pred(c => c.isLetterOrDigit || c == '-'))
).parse(input) match {
  case Success((rest, (first, second))) =>
    Success((rest, first + second.mkString))
  case Failure(exception) => Failure(ParseError(input))
}
```

`oneOrMore`可以重写为，

```scala
def oneOrMore[A](parser: Parser[A]): Parser[Vector[A]] = {
  pair(parser, zeroOrMore(parser)).map(
    { case (head: A, tail: Vector[A]) => head +: tail }
  )
}
```

可以发现大部分的算子都用到了`map`、`flatMap`、`pair`、`pred`，`pair`有时候也叫`combine`，`pred`有时候叫`filter`，你可能已经在各种编程语言中找到这些算子的影子。有了这些基础算子，你就可以按照自己的喜好构筑自己的应用算子，这就是基础的重要性，或许这就是老子所说的“一生二，二生三，三生万物”吧。

[完整代码](https://gist.github.com/naosense/e398b49dfa2e4bb964de97b8a63a670b)
