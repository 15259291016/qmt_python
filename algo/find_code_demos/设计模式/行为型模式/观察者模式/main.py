# 观察者接口

from abc import ABC, abstractmethod

class Observer(ABC):
    @abstractmethod
    def update(self, temperature):
        pass
    
# 主题接口
class Subject(ABC):
    @abstractmethod
    def register_observer(self, observer):
        pass

    @abstractmethod
    def remove_observer(self, observer):
        pass

    @abstractmethod
    def notify_observers(self, temperature):
        pass

# 具体主题
class WeatherStation(Subject):
    def __init__(self):
        self._observers = []
        self._temperature = 0

    def register_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def notify_observers(self, temperature):
        for observer in self._observers:
            observer.update(temperature)

    def set_temperature(self, temperature):
        self._temperature = temperature
        self.notify_observers(temperature)
# 具体观察者
class DisplayDevice(Observer):
    def update(self, temperature):
        print(f"Temperature: {temperature}°C")
# 使用观察者模式
def main():
    weather_station = WeatherStation()

    display_device1 = DisplayDevice()
    display_device2 = DisplayDevice()

    weather_station.register_observer(display_device1)
    weather_station.register_observer(display_device2)

    weather_station.set_temperature(25)
    weather_station.set_temperature(26)

    weather_station.remove_observer(display_device1)
    weather_station.set_temperature(27)

if __name__ == "__main__":
    main()