class StateMachine:
    def __init__(self):
        self.states = ['idle', 'run', 'wait']
        self.current_index = 0
        self.current_state = self.states[self.current_index]
        self.state_counter = 600

    def delay(self):
        if self.state_counter <= 0:
            return True
        if self.current_state != 'wait':
            return True
        self.state_counter -= 1
        return False

    def next(self):
        if self.delay():
            self.current_index = (self.current_index+1) % 3
            self.current_state = self.states[self.current_index]

    def back(self):
        self.current_index = (self.current_index-1) % 3
        self.current_state = self.states[self.current_index]

    def get(self):
        return self.current_state
