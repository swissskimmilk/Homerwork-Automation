import turtle

t = turtle.Turtle()
t.speed(0)
t.ht()
t.up()
turtle.delay(0)
turtle.screensize(1024, 1024)

with open("Output/turtle.txt") as txt:
    a = txt.readlines()
    # delay = False
    for i in a:
        i = i.strip()
        if i == "stop" or i == "end":
            t.up()
        else:
            x, y = map(int, i.split(","))
            t.goto(x - 512, -(y - 512))
            t.down()
input()
