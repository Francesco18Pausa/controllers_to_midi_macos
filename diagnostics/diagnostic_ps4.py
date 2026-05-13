import pygame

pygame.init()
pygame.joystick.init()

j = pygame.joystick.Joystick(0)
j.init()

print("Controller:", j.get_name())
print("Buttons:", j.get_numbuttons())
print("Axes:", j.get_numaxes())
print("Hats:", j.get_numhats())

IGNORED = {4, 5}  # L2 e R2
    
while True:
    pygame.event.pump()

    for b in range(j.get_numbuttons()):
        if j.get_button(b):
            print("BUTTON:", b)

    for a in range(j.get_numaxes()):
        if a in IGNORED:
            continue

        v = j.get_axis(a)
        if abs(v) > 0.15:
            print("AXIS:", a, round(v, 2))

    for h in range(j.get_numhats()):
        hat = j.get_hat(h)
        if hat != (0, 0):
            print("HAT:", h, hat)

            
