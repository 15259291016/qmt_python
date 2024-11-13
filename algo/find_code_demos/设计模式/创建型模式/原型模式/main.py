'''
Date: 2024-08-27 11:23:06
LastEditors: 牛智超
LastEditTime: 2024-08-27 11:23:11
FilePath: \国金项目\algo\在网上找的代码\设计模式\创建型模式\原型模式\main.py
'''
import copy

# 抽象原型
class Document:
    def __init__(self, text, image):
        self.text = text
        self.image = image

    def clone(self):
        """返回一个自身的浅拷贝"""
        return copy.copy(self)

    def deep_clone(self):
        """返回一个自身的深拷贝"""
        return copy.deepcopy(self)

    def display(self):
        print(f"Text: {self.text}")
        print(f"Image: {self.image}")


# 具体原型
class TextDocument(Document):
    def __init__(self, text, image=None):
        super().__init__(text, image)


# 使用原型模式
if __name__ == "__main__":
    # 创建一个原始文档
    original_document = TextDocument("Hello, World!", "image.png")
    original_document.display()

    # 使用浅拷贝创建一个新文档
    shallow_copied_document = original_document.clone()
    shallow_copied_document.display()

    # 修改原始文档
    original_document.text = "Modified text"
    original_document.display()

    # 显示浅拷贝文档的变化
    shallow_copied_document.display()

    # 使用深拷贝创建一个新文档
    deep_copied_document = original_document.deep_clone()
    deep_copied_document.display()

    # 再次修改原始文档
    original_document.text = "Another modification"
    original_document.display()

    # 显示深拷贝文档是否发生变化
    deep_copied_document.display()