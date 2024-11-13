'''
Date: 2024-08-27 14:29:33
LastEditors: 牛智超
LastEditTime: 2024-08-27 14:30:15
FilePath: \国金项目\algo\在网上找的代码\设计模式\行为型模式\迭代器模式\main.py
'''
# 迭代器接口
from abc import ABC, abstractmethod

class Iterator(ABC):
    @abstractmethod
    def has_next(self) -> bool:
        pass

    @abstractmethod
    def next(self):
        pass

# 具体迭代器
class MenuItemIterator(Iterator):
    def __init__(self, items):
        self.items = items
        self.position = 0

    def has_next(self) -> bool:
        return self.position < len(self.items)

    def next(self):
        item = self.items[self.position]
        self.position += 1
        return item
# 聚合接口
class Menu(ABC):
    @abstractmethod
    def create_iterator(self) -> Iterator:
        pass

# 具体聚合
class BreakfastMenu(Menu):
    def __init__(self):
        self.items = ["Idli", "Dosa", "Vada", "Sambhar"]

    def create_iterator(self) -> Iterator:
        return MenuItemIterator(self.items)

class DinnerMenu(Menu):
    def __init__(self):
        self.items = ["Dal Makhani", "Naan", "Rice", "Chicken Curry"]

    def create_iterator(self) -> Iterator:
        return MenuItemIterator(self.items)
# 使用迭代器模式
def main():
    breakfast_menu = BreakfastMenu()
    dinner_menu = DinnerMenu()

    print("Breakfast Menu:")
    iterator = breakfast_menu.create_iterator()
    while iterator.has_next():
        item = iterator.next()
        print(item)

    print("\nDinner Menu:")
    iterator = dinner_menu.create_iterator()
    while iterator.has_next():
        item = iterator.next()
        print(item)

if __name__ == "__main__":
    main()