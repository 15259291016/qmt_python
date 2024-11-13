'''
Date: 2024-08-27 14:39:15
LastEditors: 牛智超
LastEditTime: 2024-08-27 14:44:14
FilePath: \国金项目\algo\在网上找的代码\设计模式\行为型模式\命令模式\main.py
'''
'''
Date: 2024-08-27 14:39:15
LastEditors: 牛智超
LastEditTime: 2024-08-27 14:39:47
FilePath: \国金项目\algo\在网上找的代码\设计模式\行为型模式\命令模式\main.py
'''
# 命令接口
from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass

# 接收者
class Light:
    def turn_on(self):
        print("Light turned on.")

    def turn_off(self):
        print("Light turned off.")

class Fan:
    def high_speed(self):
        print("Fan running at high speed.")

    def low_speed(self):
        print("Fan running at low speed.")
        
# 具体命令
class LightOnCommand(Command):
    def __init__(self, light: Light):
        self.light = light

    def execute(self):
        self.light.turn_on()

    def undo(self):
        self.light.turn_off()

class LightOffCommand(Command):
    def __init__(self, light: Light):
        self.light = light

    def execute(self):
        self.light.turn_off()

    def undo(self):
        self.light.turn_on()

class FanHighSpeedCommand(Command):
    def __init__(self, fan: Fan):
        self.fan = fan

    def execute(self):
        self.fan.high_speed()

    def undo(self):
        self.fan.low_speed()

class FanLowSpeedCommand(Command):
    def __init__(self, fan: Fan):
        self.fan = fan

    def execute(self):
        self.fan.low_speed()

    def undo(self):
        self.fan.high_speed()
        
# 调用者
class RemoteControlWithUndo:
    def __init__(self):
        self.on_commands = []
        self.off_commands = []
        self.undo_command = None

    def set_command(self, on_command: Command, off_command: Command):
        self.on_commands.append(on_command)
        self.off_commands.append(off_command)

    def on_button_was_pushed(self, slot):
        self.on_commands[slot].execute()
        self.undo_command = self.on_commands[slot]

    def off_button_was_pushed(self, slot):
        self.off_commands[slot].execute()
        self.undo_command = self.off_commands[slot]

    def undo_button_was_pushed(self):
        if self.undo_command:
            self.undo_command.undo()
            
# 使用命令模式
def main():
    remote_control = RemoteControlWithUndo()

    light = Light()
    fan = Fan()

    light_on = LightOnCommand(light)
    light_off = LightOffCommand(light)

    fan_high_speed = FanHighSpeedCommand(fan)
    fan_low_speed = FanLowSpeedCommand(fan)

    remote_control.set_command(light_on, light_off)
    remote_control.set_command(fan_high_speed, fan_low_speed)

    # 模拟按下按钮
    remote_control.on_button_was_pushed(0)  # 开灯
    remote_control.off_button_was_pushed(0)  # 关灯
    remote_control.on_button_was_pushed(1)  # 风扇高速
    remote_control.off_button_was_pushed(1)  # 风扇低速

    # 模拟按下撤销按钮
    remote_control.undo_button_was_pushed()  # 撤销上一步，恢复风扇高速
    remote_control.undo_button_was_pushed()  # 撤销上一步，恢复关灯

if __name__ == "__main__":
    main()