import uasyncio as asyncio
from machine import Pin, PWM

class Servo_SG90:
    
    DUTY_RESOLUTION = 65535
    FREQUENCY = 50

    ONE_SECOND = 1000
    ONE_MS = 1
    TWO_MS = 2
    MIN_DUTY = (DUTY_RESOLUTION // (ONE_SECOND//FREQUENCY)) * ONE_MS
    MAX_DUTY = (DUTY_RESOLUTION // (ONE_SECOND//FREQUENCY)) * TWO_MS
    DUTY_PER_DEGREE = (MAX_DUTY - MIN_DUTY) // 180 

    CENTER = 0
    PLUS_NINETY = 90
    MINUS_NINETY = -90

    def __init__(self,name : str, 
                 pin_number:int, 
                 initial_position: int = 0,
                 rotational_velocity:int = 30,
                 interpolation_model: str = 'linear'):

        # Set attributes
        self.name = name
        self.pin_number = pin_number
        self.initial_position = self._limit_range(initial_position)
        self.position = self.initial_position
        self.rotational_velocity = rotational_velocity
        if interpolation_model == 'linear':
            self.interpolation_model = interpolation_model
            self.interpolation_fn = self._steps
        else:
            raise NotImplementedError ("Only linear interpolation curtrently supported")

        # Change the state of the world
        self.servo_pwm = PWM(Pin(self.pin_number))
        self.servo_pwm.freq(Servo_SG90.FREQUENCY)
        self.servo_pwm.duty_u16(self._degrees_to_duty(self.position))
        
        # Create lock control access to this servo
        self.lock = asyncio.Lock()

    async def move_to_poistion(self, new_position:int, rotational_velocity = None):
        
        await self.lock.acquire()
        new_position = self._limit_range(new_position)
        if rotational_velocity:
            velocity = rotational_velocity
        else:
            velocity = self.rotational_velocity

        steps = self.interpolation_fn(new_position, velocity)
        for step in steps:
            self.servo_pwm.duty_u16(step)
            await asyncio.sleep_ms(10)  

        self.position = new_position  
        self.lock.release()
        
    def _limit_range(self, position: int) -> int:
        if position > Servo_SG90.PLUS_NINETY:
            return Servo_SG90.PLUS_NINETY
        elif position < Servo_SG90.MINUS_NINETY:
            return Servo_SG90.MINUS_NINETY
        else:
            return position

    def _degrees_to_duty(self, position:int) -> int:
        return Servo_SG90.MIN_DUTY + (((position + Servo_SG90.PLUS_NINETY) * (Servo_SG90.MAX_DUTY - Servo_SG90.MIN_DUTY)) // 180)

    def _steps(self, position, velocity) -> list:

        if position < self.position:
            return self._generate_step_values(position, self.position, velocity)         
        else:
            return list(reversed(self._generate_step_values(self.position, position, velocity)))
            

    def _generate_step_values(self, low:int, high:int, velocity:int) :
        delta = high - low
        duty_delta = self._degrees_to_duty(high) - self._degrees_to_duty(low)
        no_of_steps = delta * 100 // velocity 

        steps = []
        for x in range(no_of_steps):
            y = Servo_SG90.MIN_DUTY + ((duty_delta * x) // no_of_steps)
            steps.append(y) 
        return steps
        