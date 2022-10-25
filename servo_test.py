import uasyncio as asyncio
from servo_as import Servo_SG90 as Servo

async def main():
    servo1 =  Servo('Servo 1',0,Servo.CENTER) 
    print('Starting...')
    while True:
        asyncio.create_task(servo1.move_to_poistion(Servo.PLUS_NINETY))
        await asyncio.sleep(20)
        asyncio.create_task(servo1.move_to_poistion(Servo.MINUS_NINETY))
        await asyncio.sleep(20)
        

asyncio.run(main())
