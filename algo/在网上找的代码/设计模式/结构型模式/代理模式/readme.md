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
为某些开销很大的操作提供一个临时存放点。