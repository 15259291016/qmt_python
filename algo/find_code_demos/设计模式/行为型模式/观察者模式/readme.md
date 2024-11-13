代理模式（Proxy Pattern）是一种结构型设计模式，它为你提供了一个对象来控制对另一个对象的访问。这样做的目的是为了在请求到达目标对象之前，代理对象可以做一些预处理工作，比如权限验证、日志记录、缓存等。代理模式有助于在不改变原有对象的前提下扩展其功能。

代理模式的基本结构
代理模式主要包含三个角色：

Subject（主题接口/抽象主题）：定义了Real Subject（真实主题）和Proxy（代理）共同遵循的接口，使得代理能够作为真实主题的一个替代品。
RealSubject（真实主题）：定义了代理所代表的真实对象，是最终要引用的对象。
Proxy（代理）：包含了真实主题对象的引用，并且提供与真实主题相同的接口以便客户端可以通过代理间接地调用真实主题的方法。
使用场景
当你想在访问一个资源消耗较大的对象时，先通过一个花费相对较小的对象来表示，这就是所谓的懒加载。
在客户端和真实主题之间提供一个保护目标对象的访问层。
控制不同种类客户端对真实主题对象的访问权限。
为某些开销很大的操作提供一个临时存放点。观察者模式（Observer Pattern）是一种行为型设计模式，它定义了对象间的一种一对多依赖关系，当一个对象的状态发生改变时，所有依赖于它的对象都会得到通知并自动更新。观察者模式也被称为发布-订阅模式（Publish/Subscribe Pattern）或模型-视图模式（Model/View Pattern）。

### 观察者模式的基本结构

观察者模式通常包含以下几个角色：

1. **主题（Subject）**：也称为被观察者，它维护着一个观察者列表，并且在状态发生变化时通知所有的观察者。
2. **观察者（Observer）**：它是一个接口，定义了更新的方法，当主题的状态发生变化时，观察者会被通知。
3. **具体主题（Concrete Subject）**：实现主题接口，并且包含具体的业务逻辑。它负责维护观察者列表，并在状态发生变化时通知观察者。
4. **具体观察者（Concrete Observer）**：实现观察者接口，并且定义具体的更新逻辑。

### 使用场景

- 当一个对象的状态发生改变，所有依赖于它的对象都需要得到通知时。
- 当一个对象需要维护一系列依赖对象，而又不想使自己的接口与这些依赖对象耦合时。
- 当一个对象的改变需要触发一系列相关对象的改变时。

### 示例代码

下面是一个简单的观察者模式实现示例，假设我们有一个天气数据站，它可以监测温度，并且每当温度变化时，会通知所有注册的观察者（如显示设备）。

#### 观察者接口

```python
from abc import ABC, abstractmethod

class Observer(ABC):
    @abstractmethod
    def update(self, temperature):
        pass
```

#### 主题接口

```python
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
```

#### 具体主题

```python
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
```

#### 具体观察者

```python
class DisplayDevice(Observer):
    def update(self, temperature):
        print(f"Temperature: {temperature}°C")
```

#### 使用观察者模式

```python
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
```

在这个例子中：
- `Observer` 是观察者接口，定义了更新的方法。
- `Subject` 是主题接口，定义了注册、移除和通知观察者的方法。
- `WeatherStation` 是具体主题，实现了主题接口，并维护了一个观察者列表。
- `DisplayDevice` 是具体观察者，实现了观察者接口，并定义了具体的更新逻辑。

### 解释

通过观察者模式，我们可以实现对象之间的解耦。具体主题（`WeatherStation`）维护了一个观察者列表，并在状态发生变化时通知所有的观察者。观察者（`DisplayDevice`）只需关注自身的更新逻辑，而不必关心是谁通知了它。

### 优点

- 降低耦合度：观察者和主题之间的耦合度较低，因为观察者只需实现一个更新方法。
- 支持广播通信：一个主题可以有多个观察者，当主题的状态改变时，所有观察者都会收到通知。
- 灵活性：可以在运行时动态地添加或删除观察者。

### 缺点

- 如果一个主题对象有很多直接和间接的观察者，通知的级联更新会导致系统变得复杂。
- 观察者模式没有规定清楚如何撤销一个观察者的注册，可能导致内存泄漏。

### 总结

观察者模式非常适合用于需要实现对象之间的松散耦合，以及当一个对象的状态变化需要通知多个对象时。通过观察者模式，我们可以将对象的状态变化与具体的更新逻辑分离，使得系统更加灵活和可扩展。