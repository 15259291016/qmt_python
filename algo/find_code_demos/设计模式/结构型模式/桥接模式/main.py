'''
Date: 2024-08-27 11:51:29
LastEditors: 牛智超
LastEditTime: 2024-08-27 11:51:35
FilePath: \国金项目\algo\在网上找的代码\设计模式\结构型模式\桥接模式\main.py
'''
from abc import ABC, abstractmethod


# 抽象部分
class Shape(ABC):
    def __init__(self, renderer):
        self.renderer = renderer

    @abstractmethod
    def draw(self):
        pass


class RoundedRectangle(Shape):
    def draw(self):
        self.renderer.draw_rounded_rectangle()


class Square(Shape):
    def draw(self):
        self.renderer.draw_square()


class Circle(Shape):
    def draw(self):
        self.renderer.draw_circle()

# 实现部分
class Renderer(ABC):
    @abstractmethod
    def draw_square(self):
        pass

    @abstractmethod
    def draw_rounded_rectangle(self):
        pass

    @abstractmethod
    def draw_circle(self):
        pass


class VectorRenderer(Renderer):
    def draw_square(self):
        print("Drawing square as lines")

    def draw_rounded_rectangle(self):
        print("Drawing rounded rectangle as lines")

    def draw_circle(self):
        print("Drawing circle as lines")


class RasterRenderer(Renderer):
    def draw_square(self):
        print("Drawing square as pixels")

    def draw_rounded_rectangle(self):
        print("Drawing rounded rectangle as pixels")

    def draw_circle(self):
        print("Drawing circle as pixels")
        
# 使用桥接模式
if __name__ == "__main__":
    vector_renderer = VectorRenderer()
    raster_renderer = RasterRenderer()

    rounded_rectangle_vector = RoundedRectangle(vector_renderer)
    rounded_rectangle_raster = RoundedRectangle(raster_renderer)

    square_vector = Square(vector_renderer)
    square_raster = Square(raster_renderer)

    circle_vector = Circle(vector_renderer)
    circle_raster = Circle(raster_renderer)

    rounded_rectangle_vector.draw()  # Drawing rounded rectangle as lines
    rounded_rectangle_raster.draw()  # Drawing rounded rectangle as pixels

    square_vector.draw()  # Drawing square as lines
    square_raster.draw()  # Drawing square as pixels

    circle_vector.draw()  # Drawing circle as lines
    circle_raster.draw()  # Drawing circle as pixels