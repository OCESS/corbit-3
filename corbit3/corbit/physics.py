from unum.units import m, s, N, kg
import copy
import scipy
import scipy.linalg
import scipy.spatial
import math

G = 6.673 * 10 ** -11 * N * (m / kg) ** 2


def magnitude(vect, unit):
    # shorthand to work around scipy not working with units
    return unit * scipy.linalg.norm(vect.asNumber(unit))


def distance(A, B):
    return m * scipy.spatial.distance.cdist([A.displacement.asNumber(m)],
                                            [B.displacement.asNumber(m)])[0][0]


def speed(A, B):
    return magnitude(A.velocity - B.velocity, m / s)


def altitude(A, B):
    return distance(A, B) - A.radius - B.radius


def angle(A, B):
    return math.atan2((B.displacement[1] - A.displacement[1]).asNumber(),
                      (B.displacement[0] - A.displacement[0]).asNumber())


def gravitational_force(A, B):
    unit_distance = scipy.array([math.cos(angle(A, B)), math.sin(angle(A, B))])
    return G * A.mass_fun() * B.mass_fun() / distance(A, B) ** 2 * unit_distance


def Vcen(A, B):
    dist = A.displacement - B.displacement
    # the math here: (unit normal vector) * (velocity)
    return scipy.dot(dist / magnitude(dist, m), A.velocity - B.velocity)


def Vtan(A, B):
    dist = A.displacement - B.displacement
    # the math here is similar to Vcen
    dist = dist.asNumber(m)
    dist_tan = scipy.array((-dist[1], dist[0]))
    return m / s * scipy.dot(dist_tan / scipy.linalg.norm(dist_tan), (A.velocity - B.velocity).asNumber(m / s))


def Vorbit(A, B):
    return m / s * math.sqrt(
        ((B.mass_fun() ** 2 * G) / ((A.mass_fun() + B.mass_fun()) * distance(A, B))).asNumber(m ** 2 / s / s))


def semimajor_axis(A, B):
    mu = G * (A.mass_fun() + B.mass_fun())  # G(m + M)
    E = (magnitude(A.velocity - B.velocity, m / s) ** 2 / 2) - mu / magnitude(A.displacement - B.displacement, m)
    return -mu / 2 / E  # -mu/2E


def ecc(A, B):
    # this is all from the wikipedia orbital eccentricity page, btw: http://en.wikipedia.org/wiki/Orbital_eccentricity
    mu = G * (A.mass_fun() + B.mass_fun())  # G(m + M)
    E = -mu / 2 / semimajor_axis(A, B)  # -mu/2a
    h = (distance(A, B) * Vtan(A, B))  # r * Vtan
    return math.sqrt(1 + (2 * E * h ** 2) / (mu ** 2))  # sqrt(1 + (2Eh^2)/(mu^2))


def periapsis(A, B):
    peri = (1 - ecc(A, B)) * semimajor_axis(A, B)
    if peri <= A.radius + B.radius:
        return 0 * m
    else:
        return peri


def apoapsis(A, B):
    apo = (1 + ecc(A, B)) * semimajor_axis(A, B)
    if apo <= A.radius + B.radius:
        return 0 * m
    else:
        return apo


def stopping_acc(A, B):
    return 200  # TODO


def resolve_collision(A, B, time):
    """Detects and acts upon any collisions in the specified time interval between two entities
    :param A: First entity
    :param B: Second entity
    :param time: time interval over which to check if any collisions occur
    :return: None if no collision will occur in the timeframe, the two collided entities if there is a collision
    """
    # general overview of this function:
    # 1. find if the objects will collide in the given time
    # 2. if yes, calculate collision:
    # 2.1 represent velocities as normal velocity and tangential velocity
    # 2.2 do a 1D collision using the normal veloctiy
    # 2.3 add the normal and tangential velocities to get the new velocity

    scipy.seterr(divide="raise", invalid="raise")

    # for this function I make one of the objects the frame of reference
    # which means my calculations are much simplified
    displacement = A.displacement - B.displacement
    velocity = A.velocity - B.velocity
    acceleration = A.acceleration - B.acceleration
    radius_sum = A.radius + B.radius

    # this code finds when the the two entities will collide. See
    # http://www.gvu.gatech.edu/people/official/jarek/graphics/material/collisionsDeshpandeKharsikarPrabhu.pdf
    # for how I got the algorithm
    a = magnitude(velocity, m / s) ** 2
    b = m ** 2 / s * 2 * scipy.dot(displacement.asNumber(m), velocity.asNumber(m / s))
    c = magnitude(displacement, m) ** 2 - radius_sum ** 2

    try:
        t_to_impact = \
            (-b - m ** 2 / s * math.sqrt((b ** 2 - 4 * a * c).asNumber(m ** 4 / s ** 2))) / (2 * a)
    except:
        return

    if not scipy.isfinite(t_to_impact.asNumber(s)):
        return

    if t_to_impact > time or t_to_impact < 0 * s:
        return

    # at this point, we know there is a collision
    print("Collision:", A.name, "and", B.name, "in", t_to_impact)

    # for this section, basically turn the vectors into normal velocity and tangential velocity,
    # then do a 1D collision calculation, using the normal velocities
    # since a ' (prime symbol) wouldn't work, I've replaced it with a _ in variable names

    n = displacement  # normal vector
    un = n / magnitude(n, m)  # normal unit vector
    unt = copy.deepcopy(un)  # normal tangent vector
    unt[0], unt[1] = -unt[1], unt[0]  # ofc the tangent is orthogonal to the normal

    # A's centripetal velocity
    vAn = m / s * scipy.dot(un.asNumber(), A.velocity.asNumber(m / s))
    # A's tangential velocity
    vAt = m / s * scipy.dot(unt.asNumber(), A.velocity.asNumber(m / s))

    # B's centripetal velocity
    vBn = m / s * scipy.dot(un.asNumber(), B.velocity.asNumber(m / s))
    # B's tangential velocity
    vBt = m / s * scipy.dot(unt.asNumber(), B.velocity.asNumber(m / s))

    # tangent velocities are unchanged, nothing happens to them
    vAt_ = vAt
    vBt_ = vBt

    # centripetal velocities are calculated with a simple 1D collision formula
    R = 0.1

    vAn_ = \
        (A.mass_fun() * vAn + B.mass_fun() * vBn + R * B.mass_fun() * (B.velocity - A.velocity)) / \
        (A.mass_fun() + B.mass_fun())

    vBn_ = \
        (A.mass_fun() * vAn + B.mass_fun() * vBn + R * A.mass_fun() * (A.velocity - B.velocity)) / \
        (A.mass_fun() + B.mass_fun())

    # convert scalar normal and tangent velocities to vector quantities
    VAn = vAn_ * un
    VAt = vAt_ * unt

    VBn = vBn_ * un
    VBt = vBt_ * unt

    # move until the point of impact
    A.move(t_to_impact)
    B.move(t_to_impact)

    # add em up to get v'
    A.velocity = VAn + VAt
    B.velocity = VBn + VBt

    # move for the rest of the frame
    A.move(time - t_to_impact)
    B.move(time - t_to_impact)

    return [A.name, B.name]
