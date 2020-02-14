DEFAUT_DELAY = 1200


class StateMachine:
    def __init__(self):
        self.states = ['idle', 'run']
        self.current_index = 0
        self.current_state = self.states[self.current_index]
        self.state_counter = DEFAUT_DELAY

    def delay(self):
        if self.state_counter <= 0:
            self.state_counter = DEFAUT_DELAY
            return True
        if self.current_state != 'run':
            self.state_counter = DEFAUT_DELAY
            return True
        self.state_counter -= 1
        return False

    def next(self):
        if self.delay():
            self.current_index = (self.current_index+1) % 2
            self.current_state = self.states[self.current_index]

    def back(self):
        self.current_index = (self.current_index-1) % 2
        self.current_state = self.states[self.current_index]

    def get(self):
        return self.current_state
