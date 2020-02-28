class StateMachine:
    def __init__(self):
        self.states = []
        self.current_index = 0
        self.current_name = None

    def __compare_bit(self, a, b):
        if a == '*' or b == '*':
            return True
        return True if a == b else False

    def __compare_transition(self, a, b):
        if len(a) != len(b):
            return False
        for i, _ in enumerate(a):
            ia = a[i]
            ib = b[i]
            if not self.__compare_bit(ia, ib):
                return False
        return True

    def __change_state(self, trans_state):
        if self.current_name[:5] == 'init_':
            self.current_index += 1
            self.current_name = self.states[self.current_index]['name']

        if self.__compare_transition(self.states[self.current_index]['transition'], trans_state):
            return

        for index, state in enumerate(self.states):
            if self.__compare_transition(state['transition'], trans_state):
                self.current_index = index
                self.current_name = state['name']
                break

    def add_state(self, name, trans_state):
        init_state = {
            'name': 'init_' + name,
            'transition': trans_state
        }
        state = {
            'name': name,
            'transition': trans_state
        }

        self.states.append(init_state)
        self.states.append(state)
        self.current_name = self.states[self.current_index]['name']

    def set_state(self, trans_state):
        self.__change_state(trans_state)

    def get_state(self):
        return self.current_name
