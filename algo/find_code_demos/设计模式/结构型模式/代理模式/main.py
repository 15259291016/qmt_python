'''
Date: 2024-08-27 11:44:18
LastEditors: 牛智超
LastEditTime: 2024-08-27 11:44:23
FilePath: \国金项目\algo\在网上找的代码\设计模式\结构型模式\代理模式\main.py
'''
# 抽象主题
class Image:
    def display(self):
        pass


# 真实主题
class RealImage(Image):
    def __init__(self, filename):
        self.filename = filename
        self.load_from_disk()

    def load_from_disk(self):
        print(f"Loading image from disk: {self.filename}")

    def display(self):
        print(f"Displaying image: {self.filename}")


# 代理
class ProxyImage(Image):
    def __init__(self, filename):
        self.filename = filename
        self.real_image = None

    def display(self):
        if self.real_image is None:
            self.real_image = RealImage(self.filename)
        self.real_image.display()


# 使用代理模式
if __name__ == "__main__":
    image = ProxyImage("highres_image.jpg")

    # 第一次调用display()时，将会加载图像
    image.display()
    print("Image has been loaded to memory.")

    # 再次调用display()时，不会再加载图像，因为已经加载过了
    image.display()