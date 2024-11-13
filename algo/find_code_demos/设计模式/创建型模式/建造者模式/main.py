'''
Date: 2024-08-27 11:09:39
LastEditors: 牛智超
LastEditTime: 2024-08-27 11:09:44
FilePath: \国金项目\algo\在网上找的代码\设计模式\建造者模式\main.py
'''
from abc import ABC, abstractmethod


# 产品角色
class Burger:
    def __init__(self):
        self._ingredients = []

    def add_ingredient(self, ingredient):
        self._ingredients.append(ingredient)

    def list_ingredients(self):
        return ', '.join(self._ingredients)


# 抽象建造者
class BurgerBuilder(ABC):
    @property
    @abstractmethod
    def burger(self) -> Burger:
        pass

    @abstractmethod
    def add_bun(self):
        pass

    @abstractmethod
    def add_patty(self):
        pass

    @abstractmethod
    def add_cheese(self):
        pass

    @abstractmethod
    def add_veggies(self):
        pass


# 具体建造者
class CheeseburgerBuilder(BurgerBuilder):
    def __init__(self):
        self.reset()

    def reset(self):
        self._burger = Burger()

    @property
    def burger(self) -> Burger:
        burger = self._burger
        self.reset()
        return burger

    def add_bun(self):
        self._burger.add_ingredient('Bun')

    def add_patty(self):
        self._burger.add_ingredient('Patty')

    def add_cheese(self):
        self._burger.add_ingredient('Cheese')

    def add_veggies(self):
        self._burger.add_ingredient('Veggies')


# 指挥者
class BurgerPreparer:
    def __init__(self, builder: BurgerBuilder):
        self._builder = builder

    def prepare_cheeseburger(self):
        self._builder.add_bun()
        self._builder.add_patty()
        self._builder.add_cheese()
        self._builder.add_veggies()


# 使用建造者模式
if __name__ == "__main__":
    burger_builder = CheeseburgerBuilder()
    preparer = BurgerPreparer(burger_builder)
    preparer.prepare_cheeseburger()
    burger = burger_builder.burger
    print(f'Burger ingredients: {burger.list_ingredients()}')