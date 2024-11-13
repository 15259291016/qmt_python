'''
Date: 2024-08-27 12:02:54
LastEditors: 牛智超
LastEditTime: 2024-08-27 12:04:22
FilePath: \国金项目\algo\在网上找的代码\设计模式\结构型模式\享元模式\main.py
'''
# 抽象享元
from abc import ABC, abstractmethod


class Character(ABC):
    @abstractmethod
    def render(self, x, y):
        pass
    
# 具体享元
class ConcreteCharacter(Character):
    def __init__(self, char):
        self.char = char

    def render(self, x, y):
        print(f"Rendering character '{self.char}' at ({x}, {y})")
        
# 享元工厂
class CharacterFactory:
    _characters = {}

    @classmethod
    def get_character(cls, char):
        if char not in cls._characters:
            cls._characters[char] = ConcreteCharacter(char)
        return cls._characters[char]
    
# 客户端代码
def main():
    factory = CharacterFactory()

    # 创建并使用字符
    chars = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
    for i, char in enumerate(chars * 10):  # 重复字符10次
        c = factory.get_character(char)
        c.render(i % 10, i // 10)

if __name__ == "__main__":
    main()