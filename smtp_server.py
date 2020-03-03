import asyncio
import logging

from aiosmtpd.controller import Controller
from email_handler.Email_Handler import EmailHandler

async def amain(loop):
    cont = Controller(EmailHandler(), hostname='', port=8025)
    cont.start()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.create_task(amain(loop=loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass