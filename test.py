import uasyncio as asyncio
from servo_as import Servo_SG90 as Servo

async def main():
    servo1 =  Servo('Servo 1',1,Servo.CENTER_POINT,45) 

    while True:
        await asyncio.sleep(3)
        asyncio.create_task(servo1.move_to_position(Servo.CENTER_POINT))

        await asyncio.sleep(3)
        asyncio.create_task(servo1.move_to_position(Servo.PLUS_NINETY))

        await asyncio.sleep(3)
        asyncio.create_task(servo1.move_to_position(Servo.CENTER_POINT))

        await asyncio.sleep(3)
        asyncio.create_task(servo1.move_to_position(Servo.MINUS_NINETY))

        
asyncio.run(main())
