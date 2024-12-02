# 目标
class Appliance:
    def power_on(self, voltage):
        if voltage == 110:
            print("Appliance is powered on.")
        else:
            raise ValueError(f"Invalid voltage: {voltage}. Expected 110 volts.")
# 适配者
class EuropeanPlug:
    def supply_power(self):
        return 230
# 适配器
class VoltageAdapter:
    def __init__(self, plug):
        self._plug = plug

    def power_on(self):
        voltage = self._plug.supply_power()
        if voltage == 230:
            # 这里模拟电压转换的过程
            return 110
        return voltage
# 使用适配器模式
def main():
    appliance = Appliance()
    european_plug = EuropeanPlug()
    adapter = VoltageAdapter(european_plug)

    try:
        appliance.power_on(adapter.power_on())
    except ValueError as e:
        print(e)

if __name__ == "__main__":
    main()