###############
### IMPORTS ###
###############
from hub import port, motion_sensor
import motor
import motor_pair
import runloop
import math, time



#################
### VARIABLES ###
#################
scale = 360
coords = [0, 0]
bearing = 0
left_motor = port.A
right_motor = port.B



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

async def arc(current_coords, target_coords, look_ahead, W):
    R = 0
    t = 5
    current_angle = check_bearing()
    #current_angle = round(math.degrees(math.atan(current_bearing)), 3)
    mAB = (target_coords[1] - current_coords[1]) / (target_coords[0] - current_coords[0])
    reference_angle = round(math.atan(mAB), 3)
    change = [target_coords[0] - current_coords[0], target_coords[1] - current_coords[1]]
    if change[0] > 0 and change[1] > 0:
        wanted_angle = reference_angle
    elif change[0] < 0 and change[1] > 0:
        wanted_angle = math.pi - reference_angle
    elif change[0] > 0 and change[1] < 0:
        wanted_angle = math.pi + math.pi - reference_angle
    elif change[0] < 0 and change[1] < 0:
        wanted_angle = math.pi + reference_angle
    angle_error = round(wanted_angle - math.radians(current_angle), 3) # Ignore this warning
    if abs(angle_error) > math.pi:
        angle_error = 2 * math.pi - abs(angle_error)
    print(current_angle, math.degrees(wanted_angle), math.degrees(angle_error))
    R = (look_ahead / 2) / math.sin(angle_error)
    print(R)
    inner = R - (W / 2)
    outer = R + (W / 2)
    innerArcLength = 2 * angle_error * inner
    outerArcLength = 2 * angle_error * outer
    outer_wheel = -1 if angle_error < 0 else 1 # Ignore this warning too
    #print(current_bearing, mAB, outer_wheel)
    #print(current_angle, wanted_angle, angle_error, R)
    #print(inner, outer)
    #print(innerArcLength, outerArcLength)
    innerDeg = innerArcLength * scale
    outerDeg = outerArcLength * scale
    innerSpeed = innerDeg / t
    outerSpeed = outerDeg / t
    if outer_wheel == 1:
        motor.run_for_degrees(left_motor, int(innerDeg), int(-1 * innerSpeed))
        await motor.run_for_degrees(right_motor, int(outerDeg), int(outerSpeed))
    else:
        motor.run_for_degrees(left_motor, int(outerDeg), int(-1 * outerSpeed))
        await motor.run_for_degrees(right_motor, int(innerDeg), int(innerSpeed))
    return

def check_bearing():
    angle = motion_sensor.tilt_angles()[0] / 10
    #return 360 if (360 - (abs(angle * -1) if angle < 0 else 360 - angle)) == 0 else (360 - (abs(angle * -1) if angle < 0 else 360 - angle))
    #return 450 - (360 - (360 - (abs(angle * -1) if angle < 0 else 360 - angle)))
    return angle if angle >= 0 else 360 - abs(angle)



##########################
### FRONTEND FUNCTIONS ###
##########################
async def curve(coords, bearing, target_co_ords, look_ahead, W = 1, pure_pursuit = True, turn_at_end = True):
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
            print(coords, chosen_target)
            dist = ((chosen_target[0] - coords[0])**2 + (chosen_target[1] - coords[1])**2)**0.5
            print(look_ahead, dist)
            count += 1
            #break
            await arc(coords, chosen_target, dist, W)
            print("arc done")
            coords = chosen_target
            coords = [round(coords[0], 2), round(coords[1], 2)]

            #if count == 3:
                #print("Interrupt")
                #return
        return coords
    else:
        while ((coords[0] < target_co_ords[-1][0] and direction == 1) or (coords[0] > target_co_ords[-1][0] and direction == -1)):
            x = round(coords[0] + (direction * look_ahead), 2)
            y = round(f(x, model.coef_), 2)
            coords = await go_to(motor_pair.PAIR_1, coords, [x, y], False)
        coords = await go_to(motor_pair.PAIR_1, coords, [target_co_ords[-1][0], target_co_ords[-1][1]], False)
        if turn_at_end: await reset_bearing(motor_pair.PAIR_1)
        return coords

async def go_to(motorpair, current_coords, target_co_ords, turn = 90):
    change = [target_co_ords[0] - current_coords[0], target_co_ords[1] - current_coords[1]]
    total_move = math.sqrt(change[0] ** 2 + change[1] ** 2)
    reference_angle = round(math.degrees(math.atan(abs(change[1]/change[0]))), 3)
    current_angle = check_bearing()
    if change[0] > 0 and change[1] > 0:
        wanted_angle = reference_angle
    elif change[0] < 0 and change[1] > 0:
        wanted_angle = 180 - reference_angle
    elif change[0] > 0 and change[1] < 0:
        wanted_angle = 360 - reference_angle
    elif change[0] < 0 and change[1] < 0:
        wanted_angle = 180 + reference_angle
    angle_error = wanted_angle - current_angle # Ignore this warning
    if abs(angle_error) > 180:
        angle_error = 360 - abs(angle_error)
    print(change, reference_angle, wanted_angle, angle_error) # Ignore this warning too
    await turn_degrees(motorpair, angle_error)
    #await motor_pair.move_for_degrees(motorpair, int(total_move * scale), 0)
    #if turn:
        #angle_error_2 = turn - wanted_angle # Ignore this warning too
        #await turn_degrees(motorpair, angle_error_2 * -1)
    return target_co_ords

async def turn_degrees(motorpair, degrees):
    offset = check_bearing()
    direction = -1 if degrees > 0 else 1
    changed_angle = 0
    while abs(changed_angle) < abs(degrees):
        motor_pair.move_tank(motorpair, 180 * direction, -180 * direction)
        changed_angle = abs(check_bearing() - offset)
        if abs(changed_angle) > 180:
            changed_angle = 360 - abs(changed_angle)
    motor_pair.stop(motorpair)

async def reset_bearing(motorpair):
    current = check_bearing()
    direction = -1 if current > 180 else 1
    degrees_to_turn = current * -1
    while abs(check_bearing() - current) < abs(degrees_to_turn):
        motor_pair.move_tank(motorpair, 180 * direction, -180 * direction)
    motor_pair.stop(motorpair)


############
### MAIN ###
############
async def main(coords):
    print(check_bearing())
    motor_pair.pair(motor_pair.PAIR_1, left_motor, right_motor)
    time.sleep(5)
    await arc([0, 0], [1, 1], 1.414, 1)
    '''
    #coords = await curve(coords, 0, [coords, [2, 2], [4, 0]], 1, 1, True)
    await arc([0, 0], [0.5, 0.88], 1.01, 1)
    time.sleep(1)
    await arc([0.5, 0.88], [1.15, 1.64], 1.00, 1)
    time.sleep(1)
    await arc([1.15, 1.64], [2.14, 1.99], 1.05, 1)
    time.sleep(1)
    await arc([2.14, 1.99], [3.01, 1.49], 1.00, 1)
    time.sleep(1)
    await arc([3.01, 1.49], [3.62, 0.69], 1.00, 1)
    time.sleep(1)
    await arc([3.62, 0.69], [4.09, -0.18], 0.99, 1)
    '''
    #await go_to(motor_pair.PAIR_1, [2, 1.5])
    #arc([0, 0], [1, 1], 0, 1.414, 0.875)
    time.sleep(5)
    print(check_bearing())
runloop.run(main(coords))
