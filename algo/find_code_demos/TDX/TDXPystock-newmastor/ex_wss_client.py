import websockets
import asyncio
import ssl
import time

async def main(server):
    # ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    Headers={}
    # async with websockets.connect(server,ssl=False,ping_interval=None,Headers=Headers) as websocket:
    async with websockets.connect(server,ssl=False,ping_interval=None) as websocket:
        while True:
            send=input("send:"  )
            # time.sleep(5)
            await websocket.send(send)
            message = await websocket.recv()
            print(message)

if __name__ == '__main__':
    url = "wss://localhost:8765"
    asyncio.run(main(url))

