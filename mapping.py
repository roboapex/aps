###############
### IMPORTS ###
###############
from hub import port, motion_sensor, light_matrix
import motor
import motor_pair
import runloop
import math, time
import uasyncio as asyncio



#################
### VARIABLES ###
#################
scale = 360
coords = [0, 0]
x_loc, y_loc = 0, 0
bearing = 0
left_motor = port.A
right_motor = port.B
ROBOT_WIDTH = 0.8842
old_left_rel, old_right_rel = 0, 0


###############
### CLASSES ###
###############
class LinearRegression:
        def __init__(self, fit_intercept=True):
            self.coef_ = []

        def fit(self, X, y):
            x = self._add_intercept(X)
            self.coef_ = self._normal_equation(x, y)
            return self

        def predict(self, X):
            predicted = []
            for i in range(len(X)):
                term = 0
                X[i] = X[i][::-1]
                for j in range(len(X[i])):
                    term += X[i][j] * self.coef_[j]
                term += self.coef_[-1]
                predicted.append(term)
            return predicted

        def _add_intercept(self, X):
            final = X[:][:]
            for i in range(len(final)):
                final[i].insert(0, 1)
            return final

        def _normal_equation(self, X, y):
            '''
            Normal equation:
            β = (XᵀX)⁻¹ x (XᵀY),
            Where X is the model matrix, with n+1 columns and N rows,
                n is the desired order of polynomial regression and
                N is the number of data points, which we fill as follows:
                The first column we fill with ones.
                The second with the observed values x₁, ..., xN of the independent variable.
                The third with x₁², ..., xN² of these values.
                The fourth with x₁³, ..., xN³,
                The n+1-th column with x₁ⁿ, ..., xNⁿ
            Y is a column matrix of the values y₁ to yN, of the values of the dependant values,
            β is a column matrix of the coefficients, from a₀ to aN,
                Such that the equation is the following:
                f(x) = a₀ + a₁x + a₂x² + a₃x³ + ...
            Xᵀ is the transpose of X,
            (XᵀX)⁻¹ is the inverse of XᵀX, and
            The operation between two matrices are matrix multiplication
            '''
            XT = transpose(X)
            XTX = matrix_multiplication(XT, X)
            XTXneg1 = scalar_matrix(transpose(cofact(XTX)), 1/det(XTX))
            XTXneg1XT = matrix_multiplication(XTXneg1, XT)
            coefficients = matrix_multiplication(XTXneg1XT, y)
            coefficients = [round(float(i[0]), 5) for i in coefficients][::-1]
            return coefficients

        def score(self, x, target_y):
            ysum = 0
            for y1 in target_y:
                ysum += y1[0]
            ymean = ysum / len(target_y)
            Sres = 0
            for i in range(len(target_y)):
                Sres += (target_y[i][0] - self.predict(poly([[i] for i in [x[i][0]]], len(self.coef_) - 1))[0])**2
            Stot = 0
            for i in range(len(target_y)):
                Stot += (target_y[i][0] - ymean)**2
            R2 = 1 - (Sres / Stot)
            return R2



#########################
### BACKEND FUNCTIONS ###
#########################
def poly(x, deg):
        final = []
        for i in x:
            x_li = []
            for j in range(1, deg+1):
                x_li.append(i[0] ** j)
            final.append(x_li)
        return final

def matrix_multiplication(matrix1, matrix2):
    if len(matrix1[0]) != len(matrix2):
        raise ValueError("Number of columns in the first matrix must be equal to the number of rows in the second matrix.")
    rows1 = len(matrix1)
    cols1 = len(matrix1[0])
    cols2 = len(matrix2[0])
    result = [[0 for _ in range(cols2)] for _ in range(rows1)]
    for i in range(rows1):
        for j in range(cols2):
            for k in range(cols1):
                result[i][j] += matrix1[i][k] * matrix2[k][j]
    return result

def transpose(matrix):
    final_matrix = []
    temp_matrix = []
    for i in range(len(matrix[0])):
        for j in range(len(matrix)):
            temp_matrix.append(matrix[j][i])
        final_matrix.append(temp_matrix)
        temp_matrix = []
    return final_matrix

def det(matrix):
    if len(matrix) != len(matrix[0]): raise ValueError("Matrix is wrong.")
    if len(matrix) < 2: return matrix[0][0]
    if len(matrix) == 2: return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    det_re = 0
    for col in range(len(matrix)):
        det_re += matrix[0][col] * det([i[:col] + i[col + 1:] for i in matrix[1:]]) * (-1) ** col
    return det_re

def cofact(matrix):
    final = [[0 for _ in range(len(matrix))] for _ in range(len(matrix))]
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            resultant = [a[:j] + a[j + 1:] for a in (matrix[:i] + matrix[i + 1:])]
            final[i][j] = det(resultant)
            if (i % 2 == 0 and j % 2 != 0) or (i % 2 != 0 and j % 2 == 0): final[i][j] *= -1
    return final

def scalar_matrix(matrix, multiplicand):
    final = [[0 for _ in range(len(matrix))] for _ in range(len(matrix))]
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            final[i][j] = matrix[i][j] * multiplicand
    return final

def regress(target_co_ords):
    co_ords = target_co_ords
    x = [[i[0]] for i in co_ords]
    y = [[i[1]] for i in co_ords]
    r_sq = 0
    degree = 0
    while r_sq < 0.99999:
        degree += 1
        x_ = poly(x, degree)
        model = LinearRegression().fit(x_, y)
        r_sq = model.score(x, y)
    coefficients = model.coef_ # Warning - ignore
    equation = ""
    for i in range(degree):
        equation += str(coefficients[i]) + "x^" + str(degree - i) + " + "
    equation += str(coefficients[-1])
    print("R\u00B2 = " + str(r_sq) + ". Degree = " + str(degree))
    print("Equation: " + equation + ".")
    return model # Warning - ignores

def f(x, coefficients):
    total = 0
    for i in range(len(coefficients)):
        total += coefficients[-1 * (i + 1)] * ((x) ** i)
    return total
def c(x, r, coords):
    c1 = coords[1] + (r**2 - (x - coords[0])**2)**0.5
    c2 = coords[1] - (r**2 - (x - coords[0])**2)**0.5
    return (c1, c2)

def solve(r, division, coords, coefficients, precision):
    intersections = []
    for i in range(int((coords[0] - r) * division), int((coords[0] + r) * division + 1)):
        #print("x = " + str(i/division) + " " + str(c(i/division, r, coords)) + " " + str(f(i/division, coefficients)))
        if (abs(c(i/division, r, coords)[0] - f(i / division, coefficients)) < precision) or (abs(c(i/division, r, coords)[1] - f(i / division, coefficients)) < precision):
            #print("(" + str(i/division) + "," + str(f(i/division, coefficients)) + ") is an intercept. Error of " + str(abs(c(i/division, r, coords)[0] - f(i / division, coefficients)))+ ")")
            #print("Saving: (" + str(round(i/division, 2)) + "," + str(round(f(i/division, coefficients), 2)) + ")")
            intersections.append([round(i/division, 2), round(f(i/division, coefficients), 2)])
    return intersections

def update_coords(coords, bearing):
    print("New Coords: " + str(coords) + " | Bearing: " + str(bearing))
    #| Angle: {math.degrees(math.atan(bearing))}

async def arc(target_coords):
    global coords
    W = ROBOT_WIDTH
    local_x, local_y = 0, 0
    R = 0
    current_angle = check_bearing()
    change = [target_coords[0] - coords[0], target_coords[1] - coords[1]]
    if not 0 in change:
        mAB = change[1] / change[0]
        reference_angle = abs(math.atan(mAB))
        change = [target_coords[0] - coords[0], target_coords[1] - coords[1]]
        if change[0] > 0 and change[1] > 0:
            wanted_angle = reference_angle
        elif change[0] < 0 and change[1] > 0:
            wanted_angle = math.pi - reference_angle
        elif change[0] > 0 and change[1] < 0:
            wanted_angle = math.pi + math.pi - reference_angle
        elif change[0] < 0 and change[1] < 0:
            wanted_angle = math.pi + reference_angle
        angle_error = wanted_angle - math.radians(current_angle) # Ignore this warning
        if abs(angle_error) > math.pi:
            angle_error = 2 * math.pi - abs(angle_error)
        print(current_angle, math.degrees(wanted_angle), math.degrees(angle_error)) # Ignore this warning too
        R = ((change[0]**2 + change[1]**2)**0.5 / 2) / math.sin(abs(angle_error))
        base_angles = math.pi - 2 * angle_error
        turning_angle = math.pi - base_angles
    else:
        wanted_angle = math.pi
        angle_error = math.pi
        R = max(change[0]/2, change[1]/2)
        turning_angle = math.pi
    print(R)
    tracking_movement = turning_angle * R
    innerArcLength = tracking_movement - ((W / 2) * turning_angle)
    outerArcLength = tracking_movement + ((W / 2) * turning_angle)
    innerDeg = innerArcLength * scale
    outerDeg = outerArcLength * scale
    innerSpeed = innerDeg / 5
    outerSpeed = outerDeg / 5
    print(tracking_movement, innerArcLength, outerArcLength)
    outer_wheel = -1 if angle_error < 0 else 1
    if outer_wheel == 1:
        motor.run_for_degrees(left_motor, int(innerDeg), int(-1 * innerSpeed))
        await motor.run_for_degrees(right_motor, int(outerDeg), int(outerSpeed))
    else:
        motor.run_for_degrees(left_motor, int(outerDeg), int(-1 * outerSpeed))
        await motor.run_for_degrees(right_motor, int(innerDeg), int(innerSpeed))
    print(current_angle, check_bearing(), math.degrees(turning_angle), W)
    if abs(check_bearing() - math.degrees(turning_angle) - current_angle) > 2: # Correcting mistakes from too high speed
        turning_angle = math.radians(check_bearing() - math.degrees(turning_angle) - current_angle)
        tracking_movement = turning_angle * R
        innerArcLength = tracking_movement - ((W / 2) * turning_angle)
        outerArcLength = tracking_movement + ((W / 2) * turning_angle)
        innerDeg = innerArcLength * scale
        outerDeg = outerArcLength * scale
        innerSpeed = innerDeg / 1
        outerSpeed = outerDeg / 1
        if check_bearing() - math.degrees(turning_angle) - current_angle > 0:
            print("Overshot")
            if outer_wheel == 1:
                motor.run_for_degrees(left_motor, int(innerDeg), int(innerSpeed))
                await motor.run_for_degrees(right_motor, int(outerDeg), -1 * int(outerSpeed))
            else:
                motor.run_for_degrees(left_motor, int(outerDeg), int(outerSpeed))
                await motor.run_for_degrees(right_motor, int(innerDeg), -1 * int(innerSpeed))
        else:
            print("Undershot")
            if outer_wheel == 1:
                motor.run_for_degrees(left_motor, int(innerDeg), -1 * int(innerSpeed))
                await motor.run_for_degrees(right_motor, int(outerDeg), int(outerSpeed))
            else:
                motor.run_for_degrees(left_motor, int(outerDeg), -1 * int(outerSpeed))
                await motor.run_for_degrees(right_motor, int(innerDeg), int(innerSpeed))
    """
    left_distance, right_distance = motor.relative_position(left_motor) * -1 - old_left_distance, motor.relative_position(right_motor) - old_right_distance
    tracking_distance = ((abs(left_distance - right_distance) / 2) + min(left_distance, right_distance)) / scale
    final_angle = check_bearing()
    angle_turned = math.radians(abs(current_angle - final_angle))
    if angle_turned > math.pi:
        angle_turned = math.pi - angle_turned
    radius = tracking_distance / angle_turned
    chord_length = 2 * radius * math.sin(angle_turned / 2)
    reference_angle = angle_turned / 2
    local_x, local_y = (chord_length * math.cos(reference_angle)), (chord_length * math.sin(reference_angle))
    global_x, global_y = (chord_length * math.cos(reference_angle + math.radians(current_angle))), (chord_length * math.sin(reference_angle + math.radians(current_angle)))
    print("Local_change, ", local_x, local_y)
    print("Global change, ", global_x, global_y)
    print("Dead reckoning: ", target_coords[0], target_coords[1], "\nOdometry: ", coords[0] + global_x, coords[1] + global_y)
    coords = coords[0] + global_x, coords[1] + global_y
    """

def check_bearing():
    angle = motion_sensor.tilt_angles()[0] / 10
    angle = angle if angle >= 0 else 360 - abs(angle)
    return angle

def check_location():
    global coords, old_angle, old_left_rel, old_right_rel
    print(coords)
    left_distance, right_distance = motor.relative_position(left_motor) * -1 - old_left_rel, motor.relative_position(right_motor) - old_right_rel
    try:
        if left_distance * right_distance < 0: raise ValueError
        tracking_distance = ((abs(left_distance - right_distance) / 2) + min(left_distance, right_distance)) / scale
        final_angle = check_bearing()
        angle_turned = math.radians(abs(old_angle - final_angle))
        if angle_turned > math.pi:
            angle_turned = math.pi - angle_turned
        radius = abs(tracking_distance) / angle_turned
        chord_length = 2 * radius * math.sin(angle_turned / 2)
        reference_angle = angle_turned / 2
        if angle_turned <= 0.5: reference_angle = 0
        local_x, local_y = (chord_length * math.cos(reference_angle)), (chord_length * math.sin(reference_angle))
        global_x, global_y = (chord_length * math.cos(reference_angle + math.radians(old_angle))), (chord_length * math.sin(reference_angle + math.radians(old_angle)))
        #print(global_x, global_y, coords[0] + global_x, coords[1] + global_y, old_left_rel, old_right_rel)
        coords = coords[0] + global_x, coords[1] + global_y
    except:
        pass
    old_angle = check_bearing()
    old_left_rel = motor.relative_position(left_motor) * -1
    old_right_rel = motor.relative_position(right_motor)



##########################
### FRONTEND FUNCTIONS ###
##########################
async def curve(target_co_ords, look_ahead, W = 1, pure_pursuit = True, turn_at_end = True):
    global coords
    model = regress(target_co_ords)
    direction = 1 if target_co_ords[-1][0] > coords[0] else -1
    if pure_pursuit:
        count = 0
        while ((coords[0] < target_co_ords[-1][0] and direction == 1) or (coords[0] > target_co_ords[-1][0] and direction == -1)):
            possible_targets = solve(look_ahead, 100, coords, model.coef_, 0.01)
            precision = 0.05
            while len(possible_targets) == 0 or possible_targets[-1][0] < coords[0]:
                if precision >= 1:
                    possible_targets = [[coords[0] + 1, f(coords[0] + 1, model.coef_)]]
                    break
                precision *= 5
                possible_targets = solve(look_ahead, 100, coords, model.coef_, precision)
            chosen_target = possible_targets[-1]
            #print(coords, chosen_target)
            dist = ((chosen_target[0] - coords[0])**2 + (chosen_target[1] - coords[1])**2)**0.5
            #print(look_ahead, dist)
            count += 1
            #break
            await arc(chosen_target, dist, W)
            coords = chosen_target
            coords = [round(coords[0], 2), round(coords[1], 2)]
    else:
        while ((coords[0] < target_co_ords[-1][0] and direction == 1) or (coords[0] > target_co_ords[-1][0] and direction == -1)):
            x = round(coords[0] + (direction * look_ahead), 2)
            y = round(f(x, model.coef_), 2)
            print(coords, x, y)
            await go_to([x, y], False)
        if turn_at_end:
            angle_error = 0 - check_bearing()
            if abs(angle_error) > 180:
                angle_error = 360 - abs(angle_error)
            await turn_degrees(angle_error)

async def turn_to(angle_to_turn):
    angle_error = angle_to_turn - check_bearing()
    if abs(angle_error) > 180:
        angle_error = 360 - abs(angle_error)
    await turn_degrees(angle_error)
    time.sleep(0.1)
    return

async def go_to(target_co_ords, turn = 0):
    if target_co_ords == coords: print("Robot is already at target.")
    change = [target_co_ords[0] - coords[0], target_co_ords[1] - coords[1]]
    current_angle = check_bearing()
    total_move = math.sqrt(change[0] ** 2 + change[1] ** 2)
    if change[0] == 0:
        wanted_angle = 90 if change[1] > 0 else 270
    elif change[1] == 0:
        wanted_angle = 0 if change[0] > 0 else 180
    else:
        reference_angle = math.degrees(math.atan(abs(change[1]/change[0])))
        if change[0] > 0 and change[1] > 0:
            wanted_angle = reference_angle
        elif change[0] < 0 and change[1] > 0:
            wanted_angle = 180 - reference_angle
        elif change[0] > 0 and change[1] < 0:
            wanted_angle = 360 - reference_angle
        elif change[0] < 0 and change[1] < 0:
            wanted_angle = 180 + reference_angle
    await turn_to(wanted_angle)
    check_location()
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, int(total_move * scale), 0)
    check_location()
    await turn_to(turn)

async def turn_degrees(degrees):
    motorpair = motor_pair.PAIR_1
    if abs(degrees) == 180: 
        await turn_degrees(90)
        await turn_degrees(90)
        return
    offset = check_bearing()
    direction = 1 if degrees > 0 else -1
    direction *= -1
    changed_angle = 0
    while abs(changed_angle) < abs(degrees):
        motor_pair.move_tank(motorpair, 180 * direction, -180 * direction)
        changed_angle = abs(check_bearing() - offset)
        if changed_angle > 180:
            changed_angle = 360 - changed_angle
    motor_pair.stop(motorpair)


############
### MAIN ###
############
motor.reset_relative_position(left_motor, 0)
motor.reset_relative_position(right_motor, 0)
async def main():
    global coords, old_angle
    old_angle = check_bearing()
    motor_pair.pair(motor_pair.PAIR_1, left_motor, right_motor)
    #await arc([1, 1])
    #await turn_to(90)
    await go_to([1, 1])

async def checking():
    while True:
        check_location()
        time.sleep(0.5)

async def sync_start():
    await asyncio.gather(
        main(),
        checking()
    )

asyncio.run(sync_start())