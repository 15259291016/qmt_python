import asyncio
import websockets
import ssl


class WebSocketServer:
    @staticmethod  # 一定要定义为staticmethod 或把方法移出class ,不然客户端无法正常连接
    async def websocket_handler(websocket, path):
        while True:
            try:
                # 接收客户端消息
                print(websocket)
                message = await websocket.recv()
                print(f"Received message: {message}")

                # 根据接收到的消息作出响应
                if message == "Hello, Server!":
                    await websocket.send("Hello, Client!")
                elif message == "How are you, Server?":
                    await websocket.send("I'm fine, thank you!")
                elif message == "Goodbye, Server!":
                    await websocket.send("Goodbye, Client!")
                    break  # 结束循环，关闭连接
                else:
                    await websocket.send("Sorry, I didn't understand that.")
            except websockets.exceptions.ConnectionClosed:
                print("Connection with client closed")
                break

    # 定义处理连接的异步函数
    # 创建 WebSocket 服务器
    # start_server = websockets.serve(websocket_handler, "localhost", 8765)
    # start_server.__await__()
    # start_server = websockets.serve(websocket_handler, "localhost", 8765, ssl=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER))
    start_server = websockets.serve(websocket_handler, "localhost", 8765, ssl=None, ping_interval=None)
    print("WebSocket server started")
    # 运行 WebSocket 服务器
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    sockserver = WebSocketServer()
