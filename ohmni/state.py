class StateMachine:
    def __init__(self):
        self.states = ['idle', 'run', 'wait']
        self.current_index = 0
        self.current_state = self.states[self.current_index]

    def next(self):
        self.current_index = (self.current_index+1) % 3
        self.current_state = self.states[self.current_index]

    def get(self):
        return self.current_state
