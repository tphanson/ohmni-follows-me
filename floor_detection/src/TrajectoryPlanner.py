import numpy as np

class TrajectoryPlanner:
    def __init__(self, x, y, v_left, v_right, theta, l, sample_time):
        # Init all parameters
        self.x = x
        self.y = y
        self.v_left = v_left*0.43
        self.v_right = v_right*0.43
        print("V left is: {}, V right is: {}".format(self.v_left, self.v_right))
        self.theta = theta
        self.L = l
        self.sample_time = sample_time
        self.current_time = 0
        self.path_x = [x]
        self.path_y = [y]
        
        self.x_left = x - l*10
        self.y_left = y
        self.x_right = x + l*10
        self.y_right = y

        self.path_x.append(self.x_left)
        self.path_x.append(self.x_right)

        self.path_y.append(self.y_left)
        self.path_y.append(self.y_right)

    def update_parameters(self, v_right, v_left):
        w_dir = (v_right - v_left) / (2 * self.L*10)
        v_dir = (v_right + v_left) / 2
        self.theta = self.theta + w_dir

        # Update new position
        self.x = self.x + v_dir * np.cos(self.theta)
        self.y = self.y + v_dir * np.sin(self.theta)
        
        self.x_left = self.x_left + v_dir * np.cos(self.theta)
        self.x_right = self.x_right + v_dir * np.cos(self.theta)

        self.y_left = self.y_left + v_dir * np.sin(self.theta)
        self.y_right = self.y_right + v_dir * np.sin(self.theta)

        # Add new position to path
        self.path_x.append(self.x)
        self.path_y.append(self.y)
        
        #self.path_x.append(self.x_left)
        #self.path_y.append(self.y_left)

        #self.path_x.append(self.x_right)
        #self.path_y.append(self.y_right)

    def run(self, v_right, v_left, limit_time):
        while self.current_time < limit_time:
            self.current_time += self.sample_time
            self.update_parameters(v_right, v_left)


if __name__ == '__main__':
    my_robot = TrajectoryPlanner(0, 0, 0, 0, 0, 3.5, 0.1)
    my_robot.run(42, 36, 7) 

