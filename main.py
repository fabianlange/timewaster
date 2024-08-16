import asyncio
import random
import string
from itertools import batched

response_body = """HTTP/1.1 200 OK
Server: Apache/2.2.8 (Ubuntu) mod_ssl/2.2.8 OpenSSL/0.9.8g
Content-Length: {length}
Connection: close
Content-Type: text/html

{content}"""


def generate_response_body():
    length = random.randint(1024, 1024 * 100)
    content = "".join(
        [
            random.choice(string.ascii_uppercase + string.ascii_lowercase)
            for _ in range(length)
        ]
    )

    return response_body.format(content=content, length=length)


async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info("peername")

    print(f"Received {message!r} from {addr!r}")

    response = generate_response_body()
    print(f"Send: {response!r}")

    for chunk in batched(response, 100):
        chunk = "".join(chunk)
        writer.write(chunk.encode())
        await writer.drain()
        await asyncio.sleep(0.1)

    print("Close the connection")
    writer.close()
    await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_echo, "127.0.0.1", 8888)

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


asyncio.run(main())
