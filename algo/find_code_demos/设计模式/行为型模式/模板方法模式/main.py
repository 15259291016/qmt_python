# 抽象类
from abc import ABC, abstractmethod

class GameTask(ABC):
    def template_method(self):
        self.step_one()
        self.step_two()
        self.step_three()
        self.hook_method()

    @abstractmethod
    def step_one(self):
        pass

    @abstractmethod
    def step_two(self):
        pass

    @abstractmethod
    def step_three(self):
        pass

    def hook_method(self):
        pass
    
# 具体子类
class CollectTreasureTask(GameTask):
    def step_one(self):
        print("Locate the treasure map.")

    def step_two(self):
        print("Follow the map to the treasure location.")

    def step_three(self):
        print("Collect the treasure.")

    def hook_method(self):
        print("Check for traps before collecting the treasure.")


class RescuePrincessTask(GameTask):
    def step_one(self):
        print("Find the castle.")

    def step_two(self):
        print("Sneak past the guards.")

    def step_three(self):
        print("Rescue the princess.")

    def hook_method(self):
        print("Make sure the princess is safe before leaving the castle.")
        
# 使用模板方法模式
def main():
    collect_treasure_task = CollectTreasureTask()
    rescue_princess_task = RescuePrincessTask()

    print("Collecting Treasure Task:")
    collect_treasure_task.template_method()
    print("\nRescuing Princess Task:")
    rescue_princess_task.template_method()

if __name__ == "__main__":
    main()