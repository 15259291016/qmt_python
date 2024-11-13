组合模式（Composite Pattern）是一种结构型设计模式，它允许你将对象组合成树形结构来表示“部分-整体”的层次结构。该模式使得客户端能够一致地处理单个对象和组合对象，即客户端可以用统一的方式处理叶子对象和树枝对象。

### 组合模式的基本结构

组合模式通常包含以下几个角色：

1. **抽象构件（Component）**：定义了所有节点的公共接口。此接口可能包括添加、删除、获取子节点的方法，以及定义了节点本身的业务逻辑方法。
2. **叶子（Leaf）**：在组合结构中表示叶子节点的对象。叶子对象没有子节点。
3. **树枝（Composite）**：在组合结构中表示分支节点的对象。树枝对象包含它的子节点，并且可以有树枝对象或叶子对象作为其子节点。
4. **客户端（Client）**：使用组合对象的客户端代码。

### 使用场景

- 当你需要表示一个对象的整体-部分层次结构时。
- 当你希望用户可以一致地处理个别对象和组合对象时。
- 当一个类由于需要处理多种类型的子部件而变得过于庞大或复杂时，可以考虑将这些子部件抽象成一个通用接口。

### 示例代码

下面是一个简单的组合模式实现示例，假设我们要构建一个文件系统的模型，其中包含文件夹和文件。

#### 抽象构件

```python
from abc import ABC, abstractmethod

class FileSystemNode(ABC):
    @abstractmethod
    def add(self, node):
        pass

    @abstractmethod
    def remove(self, node):
        pass

    @abstractmethod
    def display(self):
        pass
```

#### 叶子

```python
class File(FileSystemNode):
    def __init__(self, name):
        self.name = name

    def add(self, node):
        raise Exception("Cannot add to a file.")

    def remove(self, node):
        raise Exception("Cannot remove from a file.")

    def display(self):
        print(f"File: {self.name}")
```

#### 树枝

```python
class Directory(FileSystemNode):
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, node):
        self.children.append(node)

    def remove(self, node):
        self.children.remove(node)

    def display(self):
        print(f"Directory: {self.name}")
        for child in self.children:
            child.display()
```

#### 使用组合模式

```python
def main():
    root = Directory("root")
    bin = Directory("bin")
    tmp = Directory("tmp")
    usr = Directory("usr")

    root.add(bin)
    root.add(tmp)
    root.add(usr)

    users = Directory("users")
    users.add(File("joe.txt"))
    users.add(File("bill.txt"))

    usr.add(users)
    usr.add(File("scripts"))

    root.display()

if __name__ == "__main__":
    main()
```

在这个例子中：
- `FileSystemNode` 定义了所有文件系统节点的公共接口。
- `File` 实现了 `FileSystemNode` 接口，并且不允许添加或移除子节点，因为它是一个叶子节点。
- `Directory` 也实现了 `FileSystemNode` 接口，并且可以添加和移除子节点，因为它是一个树枝节点。
- 在 `main` 函数中，我们创建了一个文件系统的层次结构，并展示了如何添加和展示目录和文件。

### 解释

通过组合模式，我们能够创建一个树形结构，其中每个节点都遵循相同的接口，无论它是叶子还是树枝。这意味着我们可以编写操作 `FileSystemNode` 的代码，并且这些代码能够在不知道具体类型的情况下工作于任何 `FileSystemNode` 的实例上，无论是文件还是目录。

### 优点

- 客户端可以一致地处理树叶和树枝对象。
- 支持递归算法，方便处理整个结构。
- 更容易增加新类型的组件。

### 缺点

- 设计比较复杂，需要区分抽象构件、叶子和树枝。
- 如果对象树非常大，则可能导致性能问题，尤其是在深度遍历的情况下。

总的来说，组合模式非常适合用于处理具有层次结构的问题域，特别是当你需要以统一的方式处理整体和部分时。