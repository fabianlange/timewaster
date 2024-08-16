import asyncio
import random
import string
import time
from itertools import batched

import structlog
from dpkt.http import Request

log = structlog.get_logger()

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
    start_time = time.monotonic()
    data = await reader.read(512)
    request = Request(data)

    addr = writer.get_extra_info("peername")

    log.info(f"Received request from {addr!r} for URI {request.uri}")

    response = generate_response_body()
    log.info(f"Sending {len(response)} byte response")

    for chunk in batched(response, 100):
        chunk = "".join(chunk)
        writer.write(chunk.encode())
        await writer.drain()
        sleep_time = random.random()
        await asyncio.sleep(sleep_time)

    log.info("Closing connection")
    writer.close()
    await writer.wait_closed()

    total_time = round(time.monotonic() - start_time, 2)
    log.info(f"Finished request in {total_time} seconds")


async def main():
    server = await asyncio.start_server(handle_echo, "0.0.0.0", 8888)

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    log.info(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


asyncio.run(main())
