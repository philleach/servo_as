import uasyncio as asyncio
from machine import Pin, PWM

class Servo_SG90:
    
    DUTY_RESOLUTION = 65535
    FREQUENCY = 50

    CENTER_POINT = 0
    PLUS_NINETY = 90
    MINUS_NINETY = -90
    DEGREE_RANGE = 180

    MIN_DUTY = 2175  
    MAX_DUTY = 7575
    DUTY_RANGE = MAX_DUTY - MIN_DUTY
    DUTY_PER_DEGREE = (MAX_DUTY - MIN_DUTY) // DEGREE_RANGE 

    DEFAULT_VELOCITY = 30 # degrees per second
    DEFAULT_INTERPOLATION = 'linear'

    def __init__(self,
                 name : str, 
                 pin_number:int, 
                 initial_position: int = CENTER_POINT,
                 rotational_velocity:int = DEFAULT_VELOCITY,
                 interpolation_model: str = DEFAULT_INTERPOLATION):

        # Set attributes
        self.name = name
        self.pin_number = pin_number

        self.initial_position = self._limit_range(initial_position)

        self.position = dict()
        self.position['degrees'] = self.initial_position
        self.position['duty'] = self.degrees_to_duty(self.position['degrees'])
        self.rotational_velocity = rotational_velocity
        if interpolation_model == 'linear':
            self.interpolation_model = interpolation_model
            self.interpolation_fn = self._steps
        else:
            raise NotImplementedError ("Only linear interpolation curtrently supported")

        # Change the state of the world
        self.servo_pwm = PWM(Pin(self.pin_number))
        self.servo_pwm.freq(Servo_SG90.FREQUENCY)
        self.servo_pwm.duty_u16(self.position['duty'])
        
        print(f'{self.position}')
        # Create lock control access to this servo
        self.lock = asyncio.Lock()
    
    def degrees_to_duty(self, degrees:int) -> int:
        return self.MIN_DUTY + (((degrees + self.PLUS_NINETY) * self.DUTY_RANGE) // self.DEGREE_RANGE)

    def duty_to_degrees(self, duty:int) -> int:
        return ((duty - self.MIN_DUTY) // self.DUTY_PER_DEGREE) - self.PLUS_NINETY

    async def move_to_position(self, new_position:int, rotational_velocity_override = None):
        
        await self.lock.acquire()

        to_position = dict()
        to_position['degrees'] = self._limit_range(new_position)
        to_position['duty'] = self.degrees_to_duty(to_position['degrees'])

        if rotational_velocity_override:
            velocity = rotational_velocity_override
        else:
            velocity = self.rotational_velocity

        steps = self.interpolation_fn(self.position, to_position, velocity)
        for step in steps:
            self.servo_pwm.duty_u16(step['duty'])
            self.position = step
            await asyncio.sleep_ms(1)  

        self.lock.release()
        
    def _limit_range(self, position: int) -> int:
        if position > Servo_SG90.PLUS_NINETY:
            return Servo_SG90.PLUS_NINETY
        elif position < Servo_SG90.MINUS_NINETY:
            return Servo_SG90.MINUS_NINETY
        else:
            return position

    def _steps(self, from_position, to_position,  velocity) -> list:

        if from_position['duty'] <= to_position['duty']:
            return self._generate_step_values(from_position, to_position, velocity)         
        else:
            return list(reversed(self._generate_step_values(to_position, from_position, velocity)))
            

    def _generate_step_values(self, from_pos:dict, to_pos:dict, velocity:int) :
        
        print(f'From: {from_pos}')
        print(f'To:   {to_pos}')
 
        duty_velocity = velocity * self.DUTY_PER_DEGREE
        duty_delta = to_pos['duty']  - from_pos['duty']
        no_of_steps = (duty_delta * 1000) // duty_velocity 

        print('----------')
        print(f'Velocity:      {velocity}')
        print(f'Duty velocity: {duty_velocity}')
        print(f'Duty Delta:    {duty_delta}')
        print(f'No of steps:   {no_of_steps}')
        print('----------') 

        steps = []
        for x in range(no_of_steps):
            step = dict()
            step['duty'] = from_pos['duty'] + ((duty_delta * x) // no_of_steps)
            step['degrees'] = self.duty_to_degrees(step['duty'])
            steps.append(step) 
        return steps
        
