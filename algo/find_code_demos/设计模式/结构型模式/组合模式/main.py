'''
Date: 2024-08-27 14:04:56
LastEditors: 牛智超
LastEditTime: 2024-08-27 14:05:35
FilePath: \国金项目\algo\在网上找的代码\设计模式\结构型模式\组合模式\main.py
'''
from abc import ABC, abstractmethod
# 抽象构件
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
    
# 叶子
class File(FileSystemNode):
    def __init__(self, name):
        self.name = name

    def add(self, node):
        raise Exception("Cannot add to a file.")

    def remove(self, node):
        raise Exception("Cannot remove from a file.")

    def display(self):
        print(f"File: {self.name}")
        
# 树枝
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
            
# 使用组合模式
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