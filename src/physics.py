from entity import Entity
from sys import stderr
import scipy
import scipy.linalg as LA
from unum.units import m,s
from math import sqrt

def resolve_collision(A, B, time):
    # general overview of this function:
    # 1. find if the objects will collide in the given time
    # 2. if yes, calculate collision:
    # 2.1 represent velocities as normal velocity and tangential velocity
    # 2.2 do a 1D collision using the normal veloctiy
    # 2.3 add the normal and tangential velocities to get the new velocity

    scipy.seterr(divide="raise", invalid="raise")
    
    # for this function I make one of the objects the frame of reference
    # which means my calculations are much simplified
    
    # find the time until a possible collision, using the x-axis
    d_x = (A.displacement[0] - B.displacement[0]) - A.radius - B.radius
    #h2fix: instead of just saying "A.r - B.r", use sinusoidal functions to find how much radius to use
    print(d_x)
    v_x = A.velocity[0] - B.velocity[0]
    a_x = A.acceleration[0] - B.acceleration[0]
    # kinematics equation here:
    # d = vt + 0.5at^2, rearrange into a quadratic:
    # 0 = (0.5a)t^2 + (v)t - d, solve for t using quadratic formula:
    try:
        t_x = (-v_x + m/s*sqrt((v_x**2 + 2*a_x*d_x).asNumber(m*m/s/s)))/a_x
    except FloatingPointError:
        # resort to simple t = v/d
        try:
            t_x = d_x / v_x
        except FloatingPointError:
            return
    #print("neg =", (-v_x - sqrt(v_x**2 + 2*a_x*d_x))/a_x)
    #print("pos =", (-v_x + sqrt(v_x**2 + 2*a_x*d_x))/a_x)
    
    
    # find the time until a possible collision, using the y-axis
    d_y = (A.displacement[1] - B.displacement[1]) - A.radius - B.radius
    print("d_y",d_y)
    v_y = A.velocity[1] - B.velocity[1]
    a_y = A.acceleration[1] - B.acceleration[1]
    # kinematics equation here:
    # d = vt + 0.5at^2, rearrange into a quadratic:
    # 0 = (0.5a)t^2 + (v)t - d, solve for t using quadratic formula:
    
    try:
        t_y = (-v_y + m/s * sqrt((v_y**2 + 2*a_y*d_y).asNumber(m*m/s/s)))/a_y
    except FloatingPointError:
        # resort to simple t = v/d
        try:
            t_y = d_y / v_y
        except FloatingPointError:
            return
    #print("neg =", (-v_y - sqrt(v_y**2 + 2*a_y*d_y))/a_y)
    #print("pos =", (-v_y + sqrt(v_y**2 + 2*a_y*d_y))/a_y)
    
    
    # if there is a collision this frame, both t_x and t_y will be less than
    # the time that will elapse this frame
    #print(t_x,t_y)
    #print("HELP I NEED AN ADULT")
    
    if not scipy.isfinite(t_x.asNumber(s)) or \
       not scipy.isfinite(t_y.asNumber(s)):
        return
    
    #if t_x < time and t_x > 0:
        #print(t_x)
    #if t_y < time and t_y > 0:
        #print(t_y)

    if t_x < t_y:
        t_to_impact = t_x
    else:
        t_to_impact = t_y
    
    if t_to_impact > time or t_to_impact < 0 * s:
        return
    
    # at this point, we know there is a collision
    print("Collision:", A.name, "and", B.name)
    print("Collision:", A.name, "and", B.name)
    print("Collision:", A.name, "and", B.name)
    print("Collision:", A.name, "and", B.name)
    print("Collision:", A.name, "and", B.name)
    print("Collision:", A.name, "and", B.name)
    print("Collision:", A.name, "and", B.name)
    print("Collision:", A.name, "and", B.name)
    print("Collision:", A.name, "and", B.name)

    # move until the point of impact
    A.move(t_to_impact);
    B.move(t_to_impact);

    # for this section, basically turn the vectors into normal velocity and tangential velocity,
    # then do a 1D collision calculation, using the normal velocities
    # since a ' (prime symbol) wouldn't work, I've replaced it with a _ in variable names

    n = A.displacement - B.displacement   # normal vector
    un = n / (m*LA.norm(n.asNumber(m))) # normal unit vector
    unt = un;           # normal tangent vector
    unt[0], unt[1] = \
    -unt[1], unt[0]

    # A's centripetal velocity
    vAn = m/s * scipy.dot(un.asNumber(), A.velocity.asNumber(m/s))
    # A's tangential velocity
    vAt = m/s * scipy.dot(unt.asNumber(), A.velocity.asNumber(m/s))

    # B's centripetal velocity
    vBn = m/s * scipy.dot(un.asNumber(), B.velocity.asNumber(m/s))
    # B's tangential velocity
    vBt = m/s * scipy.dot(unt.asNumber(), B.velocity.asNumber(m/s))

    # tangent velocities are unchanged, nothing happens to them
    vAt_ = vAt
    vBt_ = vBt

    # centripetal velocities are calculated with a simple 1D collision formula
    vAn_ = \
     (vAn * (A.mass() - B.mass()) + 2*B.mass() * vBn) / (A.mass() + B.mass())

    vBn_ = \
     (vBn * (B.mass() - A.mass()) + 2*A.mass() * vAn) / (B.mass() + A.mass())

    # convert scalar normal and tangent velocities to vector quantities
    VAn = vAn_ * un
    VAt = vAt_ * unt

    VBn = vBn_ * un
    VBt = vBt_ * unt

    # add em up to get v'
    A.velocity = VAn + VAt
    B.velocity = VBn + VBt

    # move for the rest of the frame
    A.move(time - t_to_impact);
    B.move(time - t_to_impact);
