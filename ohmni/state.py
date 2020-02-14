class StateMachine:
    def __init__(self):
        self.states = ['idle', 'run', 'wait']
        self.current_index = 0
        self.current_state = self.states[self.current_index]
        self.state_counter = 600

    def delay(self, func):
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
        if self.state_counter <= 0:
            self.state_counter = 600
            return wrapper
        if self.current_state != 'wait':
            self.state_counter = 600
            return wrapper
        self.state_counter -= 1

    @delay
    def next(self):
        self.current_index = (self.current_index+1) % 3
        self.current_state = self.states[self.current_index]

    def back(self):
        self.current_index = (self.current_index-1) % 3
        self.current_state = self.states[self.current_index]

    def get(self):
        return self.current_state
