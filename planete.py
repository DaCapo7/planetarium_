# importation des modules
import time
import pygame
import sys
import math
import random
from pygame.math import Vector2
import tkinter
from tkinter import *
from tkinter import font
import threading
from win32api import GetSystemMetrics
import re
import os
from tkinter import filedialog, messagebox
import pickle

# classe qui controlle la vitesse de la simulation
class Speed:
    def __init__(self, value):
        self.value = value

    def set(self, value):
        self.value = value


# si le status est True, rien ne bouge
class PauseStatus:
    def __init__(self):
        self.paused = False


# hauteur et largeur de la fenetre
class Dimension:
    def __init__(self):
        self.h = 1000
        self.w = 1000

    def setH(self, h):
        self.h = h

    def setW(self, w):
        self.w = w


# cette classe contient l'echelle de la simulation et la position de la camera
class Scale:
    def __init__(self, scale):
        self.scale = scale
        self.CamOrigin = [0, 0]

    def setScale(self, scale):
        self.scale = scale

    def changeCamOrigin(self, x, y):
        self.CamOrigin[0] += x
        self.CamOrigin[1] += y


class Parameter:
    def __init__(self, default):
        self.value = default

    def toggle(self):
        self.value = not self.value


# tous les parametres qu'on peut changer sur le LCP
class Parameters:
    def __init__(self):
        self.music = Parameter(False)
        self.isPlaying = Parameter(True)
        self.linestoggled = Parameter(True)
        self.fusion = Parameter(False)
        self.textures = Parameter(False)


# initialisation des variables accessibles par les deux threads
pause = PauseStatus()
pause.paused = True
speed_factor = Speed(1)

Parameters = Parameters()

# dimensions de la fenetre
# global winDim
winDim = Dimension()
# global scale
original_scale = 0.00005
scale = Scale(original_scale)

# traductions de coordonées dans la réalité vers sur l'écran
def real_to_screen(x, y):
    scaledOX = (x - scale.CamOrigin[0]) * scale.scale / original_scale + winDim.w / 2
    scaledOY = (y - scale.CamOrigin[1]) * scale.scale / original_scale + winDim.h / 2
    return scaledOX, scaledOY


# ... et inversement
def screen_to_real(x, y):
    realX = (x - winDim.w / 2) * (original_scale / scale.scale) + scale.CamOrigin[0]
    realY = (y - winDim.h / 2) * (original_scale / scale.scale) + scale.CamOrigin[1]
    return realX, realY


# taille de la fenetre de simulation
def setwinsize(w, h, win):

    if auto == 1 or w.get() == "" or h.get == "":
        # taille de la simulation grace a la taille de l ecran
        c = GetSystemMetrics(1) - 100
        winDim.setW(c)
        winDim.setH(c)

        win.destroy()
    else:
        wStr = w.get()
        hStr = h.get()
        # verification que l'utilisateur entre des int
        try:
            wStr = w.get()
            hStr = h.get()
            wInt = int(wStr)
            hInt = int(hStr)

            winDim.setW(wInt)
            winDim.setH(hInt)

            win.destroy()
        except:
            Label(win, text="Enter an integer please", bg="black", fg="red").grid(
                row=5, column=0, sticky="w"
            )


def update_fps(clock, how="indirect"):
    # fonction pour afficher les fps (frame per second = nombre d'images affichées chaque secondes)
    if how == "direct":
        fps = str(round(clock.get_fps(), 3)) + " fps"
        return fps
    elif how == "indirect":
        fps = str(int(clock.get_fps())) + " fps"
    else:
        fps = "ERROR"
    # fps en rouge si mauvaises performances
    if clock.get_fps() > 60:
        color = (0, 255, 0)
    else:
        color = (255, 0, 0)
    fps_text = littlefont.render(fps, True, pygame.Color(color))
    return fps_text


# fonction pour changer l'échelle de la simulation
def change_scale(factor):
    scale.setScale(scale.scale * factor)


# masse volumique de materiaux (kg/m3)
materials = {
    "Jupiter": 1326,
    "Mercure": 5427,
    "Neptune": 1638,
    "Saturne": 687,
    "Soleil": 1408,
    "Terre": 5515,
    "Uranus": 1270,
    "Venus": 5204,
    "Mars": 3933,
    # "real blackhole": 4 * 10 ** 17, # trou noir avec une vraie masse volumique (fait n'importe quoi)
    "fake blackhole": 4 * 10**7,
}

# couleurs des planetes si on choisi de ne pas afficher les textures
materials_colors = {
    "Jupiter": (231, 76, 60),
    "Mercure": (229, 152, 102),
    "Neptune": (169, 204, 227),
    "Saturne": (245, 176, 65),
    "Soleil": (244, 208, 63),
    "Terre": (52, 152, 219),
    "Uranus": (174, 172, 255),
    "Venus": (247, 212, 195),
    "Mars": (255, 69, 0),
    # "real blackhole": (10, 10, 10),
    "fake blackhole": (10, 10, 10),
}

# textures personalisées
materials_filenames = {
    "Jupiter": "Jupiter.png",
    "Mercure": "Mercure.png",
    "Neptune": "Neptune.png",
    "Saturne": "Saturne.png",
    "Soleil": "Soleil.png",
    "Terre": "Terre.png",
    "Uranus": "Uranus.png",
    "Venus": "Venus.png",
    "Mars": "Mars.png",
    "fake blackhole": "blackhole.png",
}

materials_files = {}

# liste des objets planetes
planets = []

# classe d'une planete
class Planet:
    def __init__(
        self, x, y, r, material, name, vx=0, vy=0, notmoving=False, camfollow=False
    ):
        # position
        self.x = float(x)
        self.y = float(y)
        # rayon
        self.r = r
        # materiau
        self.material = material
        # masse depuis le matériau
        self.mass = int(((4 / 3) * math.pi * (self.r**3)) * materials[material])
        # nom de la planete
        self.name = name
        # vecteurs vitesses initialisables
        self.vx = vx
        self.vy = vy
        # si la planète bouge
        self.notmoving = notmoving
        if notmoving:
            self.vx = 0
            self.vy = 0
        # si la camera suit la planete
        if camfollow:
            for planet in planets:
                planet.camfollow = 0
        self.camfollow = camfollow

        # debug
        print(
            "Planet {} is {} m^3 and {} kg at x = {} and y = {} and notmoving = {}".format(
                self.name,
                int(((4 / 3) * math.pi * (r**3))),
                self.mass,
                self.x,
                self.y,
                self.notmoving,
            )
        )


# formule de newton (in: kg kg m, out: N)
def gravity(m1, m2, d):
    G = 6.67 * (10**-11)

    # pas de division par 0
    if d == 0:
        return 0

    return G * ((m1 * m2) / (d**2))


# pour verifier si une input est un nombre
def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False


# met a jour les vecteurs vitesse des planetes
def updatevector(planets_list, deltatime):
    # parcourt toutes les planettes
    for selected_planet in planets_list:
        if not selected_planet.notmoving:
            # copie la planete pour la modifier
            reference_planets = planets_list.copy()
            reference_planets.remove(selected_planet)

            # création de vecteurs vierges
            fx = 0
            fy = 0

            # parcourt les autres planetes pour additioner les vecteurs force entre eux
            for reference_planet in reference_planets:
                # norme en newton
                norm = gravity(
                    selected_planet.mass,
                    reference_planet.mass,
                    math.sqrt(
                        (reference_planet.x - selected_planet.x) ** 2
                        + (reference_planet.y - selected_planet.y) ** 2
                    ),
                )

                dir_x = reference_planet.x - selected_planet.x
                dir_y = reference_planet.y - selected_planet.y

                direction = Vector2(dir_x, dir_y).normalize()
                fx += direction.x * norm
                fy += direction.y * norm

            # a = F / m
            ax = fx / selected_planet.mass
            ay = fy / selected_planet.mass

            # deltav = deltat * a
            dvx = ax * deltatime
            dvy = ay * deltatime

            selected_planet.vx += dvx
            selected_planet.vy += dvy


# bouge les planetes avec leur vecteur vitesse precedement calculé
def move_planets(planets_list, deltatime):
    collisions_list = []

    # si une planete touche le bord elle repart avec une moins grande vitesse
    for i, selected_planet in enumerate(planets_list):

        # collision avec le bord (plus utilisé)
        """if selected_planet.x > winDim.w:
            selected_planet.vx = abs(selected_planet.vx) * -0.7
        elif selected_planet.x < 0:
            selected_planet.vx = abs(selected_planet.vx) * 0.7

        if selected_planet.y > winDim.w:
            selected_planet.vy = abs(selected_planet.vy) * -0.7
        elif selected_planet.y < 0:
            selected_planet.vy = abs(selected_planet.vy) * 0.7"""

        # crée une liste de collision entre les planetes
        for j, reference_planet in enumerate(planets_list):
            if j != i:  # on vérifie que deux planetes differentes se touchent
                actual_d = math.sqrt(
                    (reference_planet.x - selected_planet.x) ** 2
                    + (reference_planet.y - selected_planet.y) ** 2
                )
                min_d = (reference_planet.r + selected_planet.r) * original_scale
                potential_collision = min(i, j), max(i, j), min_d, actual_d
                if actual_d <= min_d and potential_collision not in collisions_list:
                    # ajout de la planete à une liste de collision a faire plus tard
                    collisions_list.append(potential_collision)

    for collision in collisions_list:

        p1 = planets_list[collision[0]]
        p2 = planets_list[collision[1]]

        # eloigne les planetes si elles sont superposées
        if collision[2] - collision[3] > 3:
            if p1.mass < p2.mass:
                toadd = Vector2(p1.x - p2.x, p1.y - p2.y)
                toadd.scale_to_length(collision[2])
                p1.x = toadd.x + p2.x
                p1.y = toadd.y + p2.y
            else:
                toadd = Vector2(p2.x - p1.x, p2.y - p1.y)
                toadd.scale_to_length(collision[2])
                p2.x = toadd.x + p1.x
                p2.y = toadd.y + p1.y

        # cas no 1 : aucune des planetes n'a l attribut notmoving
        if not p1.notmoving and not p2.notmoving:

            v1 = Vector2(p1.vx, p1.vy)
            v2 = Vector2(p2.vx, p2.vy)

            c1 = Vector2(p1.x, p1.y)
            c2 = Vector2(p2.x, p2.y)

            m1 = p1.mass
            m2 = p2.mass

            # si l'utilisateur le veut, les planetes peuvent fusionner
            if Parameters.fusion.value:
                # on calcule les energies cinétiques des planetes
                Ec1 = Vector2(p1.vx**2 / m1, p1.vy**2 / m1)
                Ec2 = Vector2(p2.vx**2 / m2, p2.vy**2 / m2)

                # puis la force de collision entre elles
                collisionX = abs(Ec1.x - Ec2.x)
                collisionY = abs(Ec1.y - Ec2.y)
                LongueurCollision = (collisionX**2 + collisionY**2) ** 0.5
                print(collisionX, collisionY, LongueurCollision)

                # si la force de collision des deux planetes dépasse un certain palier, elles fusionnent
                if LongueurCollision > 1 * 10**-7:
                    # la plus lourde des deux est prioritaire
                    if m1 > m2:
                        mat = p1.material
                        name = p1.name
                        notmoving = p1.notmoving
                    else:
                        mat = p2.material
                        name = p2.name
                        notmoving = p2.notmoving

                    r = ((m1 + m2) / (4 * math.pi / 3 * materials[mat])) ** (1 / 3)

                    newPlanet = Planet(
                        (p1.x * m1 + p2.x * m2) / (m1 + m2),
                        (p1.y * m1 + p2.y * m2) / (m1 + m2),
                        r,
                        mat,
                        name,
                        vx=(p1.vx * m1 + p2.vx * m2) / (m1 + m2),
                        vy=(p1.vy * m1 + p2.vy * m2) / (m1 + m2),
                        notmoving=False,
                    )

                    planets_list.pop(max(collision[0], collision[1]))
                    planets_list.pop(min(collision[0], collision[1]))

                    planets_list.append(newPlanet)
                    continue

            # calcul des collision elastiques (aucune perte d'energie)
            # https://en.wikipedia.org/wiki/Elastic_collision

            v1new = v1 - ((2 * m2) / (m1 + m2)) * (
                Vector2(v1 - v2).dot(Vector2(c1 - c2))
            ) / Vector2(c1 - c2).magnitude_squared() * (c1 - c2)
            v2new = v2 - ((2 * m1) / (m1 + m2)) * (
                Vector2(v2 - v1).dot(Vector2(c2 - c1))
            ) / Vector2(c2 - c1).magnitude_squared() * (c2 - c1)

            # possibilité de perdre de la vitesse en collision (changer loose factor)
            force_loose_factor = 1
            p1.vx, p1.vy = v1new.x * force_loose_factor, v1new.y * force_loose_factor
            p2.vx, p2.vy = v2new.x * force_loose_factor, v2new.y * force_loose_factor
        # cas no 2 : seule l'une des deux l'a
        elif not p1.notmoving or not p2.notmoving:
            v1 = Vector2(p1.vx, p1.vy)
            v2 = Vector2(p2.vx, p2.vy)

            c1 = Vector2(p1.x, p1.y)
            c2 = Vector2(p2.x, p2.y)

            m1 = p1.mass
            m2 = p2.mass
            
            # calcul des collision elastiques (aucune perte d'energie)
            # https://en.wikipedia.org/wiki/Elastic_collision
            # m2 = double de la masse de la planete dont on calcule le vecteur
            v1new = v1 - ((4 * m1) / (m1 + 2 * m1)) * (
                Vector2(v1 - v2).dot(Vector2(c1 - c2))
            ) / Vector2(c1 - c2).magnitude_squared() * (c1 - c2)
            v2new = v2 - ((4 * m2) / (2 * m2 + m2)) * (
                Vector2(v2 - v1).dot(Vector2(c2 - c1))
            ) / Vector2(c2 - c1).magnitude_squared() * (c2 - c1)

            # conservation des forces (une ne bouge pas et l autre conserve sa vitesse initiale)
            v1new = Vector2(v1new).normalize() * Vector2(v1).magnitude()
            v2new = Vector2(v2new).normalize() * Vector2(v2).magnitude()

            force_loose_factor = 1
            p1.vx, p1.vy = v1new.x * force_loose_factor, v1new.y * force_loose_factor
            p2.vx, p2.vy = v2new.x * force_loose_factor, v2new.y * force_loose_factor

    for selected_planet in planets_list:
        # chaque planete se deplace en fonction de deltatime
        selected_planet.x += selected_planet.vx * deltatime * original_scale
        selected_planet.y += selected_planet.vy * deltatime * original_scale


# supprimer une planete
def delete_planet(index, window_ref):
    planets.pop(index)
    window_ref.destroy()


# ajouter une planete
def addplanet(
    x, y, ray, vx, vy, name, material, window_ref, notmoving, camfollow, edited=None
):
    # fenetre aui s'ouvre en ajoutant une planete
    # vérifie que les input sont valides
    if x == 0 or not isfloat(x):
        x = random.randrange(0, winDim.w)
    if y == 0 or not isfloat(y):
        y = random.randrange(0, winDim.h)
    if not re.match("^[+-]?([0-9]*[.])?[0-9]+$", ray) or float(ray) == 0:
        ray = (
            float(random.randrange(15000000, 200000000)) / 100000000
        )  # beaucoup de possibilités de nombres aléatoires
    if not re.match("^[+-]?([0-9]*[.])?[0-9]+$", vx):
        vx = 0
    if not re.match("^[+-]?([0-9]*[.])?[0-9]+$", vy):
        vy = 0
    if material.get() == "none":
        # si aucun matériel choisi : un au hasard sans les trou noirs
        material_random = list(materials.keys())

        material_random.remove("fake blackhole")
        material.set(random.choice(list(material_random)))

    # on supprime la planete originale si c'est un edit
    if edited is not None:
        planets.pop(edited)

    # ajoute la planete dans la liste
    planets.append(
        Planet(
            float(x),
            float(y),
            int(float(ray) * 10**6),
            material.get(),
            name,
            vx=int(float(vx) * 10**6),
            vy=int(float(vy) * 10**6),
            notmoving=notmoving,
            camfollow=camfollow,
        )
    )

    window_ref.destroy()


# fonction pour faire tourner la planete et changer des textes
def update_lcp(ind, lcp, label, frames, frameCnt, scaleStrVar):
    # update l'echelle
    scaleStrVar.set("Scale : " + str(float(scale.scale) / original_scale))
    # faire avancer le gif
    frame = frames[ind]
    ind += 1
    if ind == frameCnt:
        ind = 0
    label.configure(image=frame)
    lcp.after(100, update_lcp, ind, lcp, label, frames, frameCnt, scaleStrVar)


# un parametre devient true si il est false et inversement
def toggleParam(param, strvar):
    param.toggle()
    print(param.value)
    strvar.set("ON" if param.value else "OFF")


# pour enregistrer une configuration sur l'ordinateur
def savefile(strvar):
    setpause(True, strvar)
    file = filedialog.asksaveasfile(
        mode="wb",
        filetypes=[("planetarium file", ".ptrm")],
        defaultextension=".ptrm",
        initialdir="./",
        initialfile="save.ptrm",
    )
    if file is not None:
        pickle.dump(planets, file)
        file.close()
    setpause(False, strvar)


# pour ouvrir un fichier
def openfile():
    file = filedialog.askopenfilename(
        filetypes=[("planetarium file", ".ptrm")],
        defaultextension=".ptrm",
        initialdir="./",
        initialfile="save.ptrm",
    )
    if file is not None:
        with open(file, "rb") as f:
            b = pickle.load(f)
            planets.clear()
            for i in b:
                planets.append(i)


# pour effacer tout d'un coup
def clearall():
    answer = tkinter.messagebox.askyesno(
        "Confirmation", "Are you sure that you want to reset Planetarium ?"
    )
    if answer:
        planets.clear()


# fenetre tkinter qui controle les planetes sur la fenetre principale
def live_control_pad():
    lcp = tkinter.Tk()
    big_font = tkinter.font.Font(family="Helvetica", size=20, weight="bold")
    lcp.title("Live Control Pad")
    lcp.geometry("500x700")
    lcp.configure(background="Black")

    menubar = Menu(lcp)
    filemenu = Menu(menubar, tearoff=0)

    lcp.columnconfigure(tuple(range(2)), weight=1)
    lcp.rowconfigure(tuple(range(30)), weight=1)

    Label(
        lcp,
        text="Welcome Live Control Pad !",
        bg="black",
        fg="white",
        font=big_font,
        anchor="center",
    ).grid(row=0, columnspan=3, sticky="we")
    gifEarth = Label(lcp, bg="black")
    gifEarth.grid(row=1, column=1, sticky="w")

    speed_stringvar = StringVar()
    speed_stringvar.set("Speed : " + str(speed_factor.value))

    scale_stringvar = StringVar()
    scale_stringvar.set("Scale : " + str(scale.scale))

    paused_strvar = StringVar()
    paused_strvar.set("Paused" if pause.paused else "Playing")

    # Controle de la vitesse
    Button(
        lcp,
        text=" - ",
        anchor="center",
        command=lambda: change_speed(speed_stringvar, -1),
    ).grid(row=3, column=0, sticky="w")
    Button(
        lcp,
        text=" + ",
        anchor="center",
        command=lambda: change_speed(speed_stringvar, 1),
    ).grid(row=3, column=2, sticky="e")
    Label(
        lcp, textvariable=speed_stringvar, bg="black", fg="white", anchor="center"
    ).grid(row=3, column=1, sticky="w")

    # Controle de la mise en pause ou play
    Button(
        lcp,
        text=" PAUSE ",
        anchor="center",
        command=lambda: setpause(True, paused_strvar),
    ).grid(row=2, column=0, sticky="w")
    Button(
        lcp,
        text=" PLAY ",
        anchor="center",
        command=lambda: setpause(False, paused_strvar),
    ).grid(row=2, column=2, sticky="e")
    Label(
        lcp, textvariable=paused_strvar, bg="black", fg="white", anchor="center"
    ).grid(row=2, column=1, sticky="w")

    # Controle de l'échelle
    scale_change_factor = 1.1
    Button(
        lcp,
        text=" - ",
        anchor="center",
        command=lambda: change_scale(1 / scale_change_factor),
    ).grid(row=4, column=0, sticky="w")
    Button(
        lcp,
        text=" + ",
        anchor="center",
        command=lambda: change_scale(scale_change_factor),
    ).grid(row=4, column=2, sticky="e")
    Label(
        lcp, textvariable=scale_stringvar, bg="black", fg="white", anchor="center"
    ).grid(row=4, column=1, sticky="w")

    # parametre de la musique
    music_strvar = StringVar()
    music_strvar.set("ON" if Parameters.music.value else "OFF")
    Label(lcp, textvariable=music_strvar, bg="black", fg="white", anchor="center").grid(
        row=5, column=1
    )
    Label(lcp, text="Music : ", bg="black", fg="white", anchor="center").grid(
        row=5, column=0, sticky="w"
    )
    Button(
        lcp,
        text="toggle",
        anchor="center",
        command=lambda: toggleParam(Parameters.music, music_strvar),
    ).grid(row=5, column=2, sticky="e")

    # parametre des vecteurs vitesses
    linestoggled_strvar = StringVar()
    linestoggled_strvar.set("ON" if Parameters.linestoggled.value else "OFF")
    Label(
        lcp, textvariable=linestoggled_strvar, bg="black", fg="white", anchor="center"
    ).grid(row=6, column=1)
    Label(lcp, text="Vectors : ", bg="black", fg="white", anchor="center").grid(
        row=6, column=0, sticky="w"
    )
    Button(
        lcp,
        text="toggle",
        anchor="center",
        command=lambda: toggleParam(Parameters.linestoggled, linestoggled_strvar),
    ).grid(row=6, column=2, sticky="e")

    # parametre des fusions
    fusion_strvar = StringVar()
    fusion_strvar.set("ON" if Parameters.fusion.value else "OFF")
    Label(
        lcp, textvariable=fusion_strvar, bg="black", fg="white", anchor="center"
    ).grid(row=7, column=1)
    Label(lcp, text="Fusion : ", bg="black", fg="white", anchor="center").grid(
        row=7, column=0, sticky="w"
    )
    Button(
        lcp,
        text="toggle",
        anchor="center",
        command=lambda: toggleParam(Parameters.fusion, fusion_strvar),
    ).grid(row=7, column=2, sticky="e")

    # parametre des textures
    textures_strvar = StringVar()
    textures_strvar.set("ON" if Parameters.textures.value else "OFF")
    Label(
        lcp, textvariable=textures_strvar, bg="black", fg="white", anchor="center"
    ).grid(row=8, column=1)
    Label(lcp, text="Textures : ", bg="black", fg="white", anchor="center").grid(
        row=8, column=0, sticky="w"
    )
    Button(
        lcp,
        text="toggle",
        anchor="center",
        command=lambda: toggleParam(Parameters.textures, textures_strvar),
    ).grid(row=8, column=2, sticky="e")

    Button(lcp, text="CLEAR", anchor="center", command=clearall).grid(row=9, column=1)

    filemenu.add_command(label="Open", command=openfile)
    filemenu.add_command(
        label="Save",
        command=lambda: savefile(paused_strvar),
    )

    menubar.add_cascade(label="File", menu=filemenu)
    lcp.configure(background="Black", menu=menubar)

    # gif de la terre qui tourne
    frameCnt = 24
    frames = [
        PhotoImage(file="rotating_earth.gif", format="gif -index %i" % i)
        for i in range(frameCnt)
    ]

    lcp.after(0, update_lcp, 0, lcp, gifEarth, frames, frameCnt, scale_stringvar)
    lcp.mainloop()


# fonction pour mettre la simulation en pause
def setpause(paused, strvar):
    pause.paused = paused
    strvar.set("Paused" if pause.paused else "Playing")


# fonction pour changer la vitesse de la simulation sur l'écran
def change_speed(strvar, to_add):
    if (
        float(strvar.get()[7:]) < 2
    ):
        to_add = 0.1 * (abs(to_add) / to_add)
    newSpeed = float(strvar.get()[7:]) + to_add
    if 0 < newSpeed <= 100:  # max = 100
        strvar.set("Speed : " + str(round(float(newSpeed), 2)))

    if 0 < float(newSpeed) < 100:
        speed_factor.set(float(newSpeed))


# vérifie si une planete est cliquée
def planet_clicked(pos):
    X = pos[0]
    Y = pos[1]

    for i, planet in enumerate(planets):
        scaledOX, scaledOY = real_to_screen(planet.x, planet.y)
        if (
            math.sqrt(((scaledOX - X) ** 2) + ((scaledOY - Y) ** 2))
            <= planet.r * scale.scale
        ):
            return i

    return None


# lancé à chaque frame
def frame(clock, screen, fond, frames_per_second, started, planet_creating, simul=True):

    # controle de la musique
    if Parameters.music.value and not Parameters.isPlaying.value:
        pygame.mixer.music.unpause()
        Parameters.isPlaying.value = True
    elif not Parameters.music.value and Parameters.isPlaying.value:
        pygame.mixer.music.pause()
        Parameters.isPlaying.value = False

    # change la position de la camera
    for planet in planets:
        if planet.camfollow:
            scale.CamOrigin = [planet.x, planet.y]
            break

    # delta time est le temps aui s est ecoulé depuis la derniere frame
    deltaTime = clock.tick(frames_per_second) / 1000.0 * speed_factor.value * 0.1
    # empeche les fps drop trop grands
    if deltaTime > 0.01:
        deltaTime = 0.01
    # fond
    screen.blit(fond, (0, 0))
    # fps
    screen.blit(update_fps(clock), (10, 0))

    if simul:
        # calcule les vecteurs vitesses
        updatevector(planets, deltaTime)
        # calcule la nouvelle position des planetes
        move_planets(planets, deltaTime)

    # dessine chaque planete a l'ecran
    for planet in planets:
        # rond de la planete
        scaledOX, scaledOY = real_to_screen(planet.x, planet.y)

        # si les textures sont autorisées
        if Parameters.textures.value and planet.material in materials_files:
            screen.blit(
                pygame.transform.scale(
                    materials_files[planet.material],
                    (2 * planet.r * scale.scale, 2 * planet.r * scale.scale),
                ),
                (scaledOX - planet.r * scale.scale, scaledOY - planet.r * scale.scale),
            )
        # sinon on dessine des cercles colorés
        else:
            pygame.draw.circle(
                screen,
                materials_colors[planet.material],
                (scaledOX, scaledOY),
                planet.r * scale.scale,
            )

        # calcul du vecteur direction de longeur fixe
        if planet.vx == 0 and planet.vy == 0:
            direction = Vector2(0, 0)
        else:
            direction = Vector2(planet.vx, planet.vy).normalize()

        echelle = winDim.w / 2

        # dessin des lignes de direction
        if Parameters.linestoggled.value:
            pygame.draw.line(
                screen,
                (255, 0, 0),
                (scaledOX, scaledOY),
                (scaledOX + direction.x * echelle, scaledOY + direction.y * echelle),
            )
        # nom de la planete done par l utilisateur
        img = littlefont.render(planet.name, True, pygame.Color((255, 255, 255)))
        screen.blit(
            img, (scaledOX - img.get_width() / 2, scaledOY - img.get_height() / 2)
        )

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # si lutilisateur clique
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            clicked_planet = planet_clicked(pygame.mouse.get_pos())
            # si il a cliqué une planete, la modifie
            if clicked_planet is not None:
                # cree une nouvelle planete avec une fenetre tkinter
                planet_got_added = True
                planet = planets[clicked_planet]
                pos = (planet.x, planet.y)
                window = tkinter.Tk()
                window.title("Edit planet no " + str(clicked_planet + 1))
                window.geometry("325x250")
                window.configure(background="Black")
                window.columnconfigure(0, weight=1)
                window.columnconfigure(1, weight=3)

                Label(
                    window,
                    text="Welcome to planet edition center !",
                    bg="black",
                    fg="white",
                ).grid(row=0, columnspan=3)

                Label(window, text="x coordinate", bg="black", fg="white").grid(
                    row=1, column=0, sticky="w"
                )
                Label(window, text="y coordinate", bg="black", fg="white").grid(
                    row=2, column=0, sticky="w"
                )
                Label(window, text="Ray (km^6)", bg="black", fg="white").grid(
                    row=3, column=0, sticky="w"
                )
                Label(window, text="vx (m/s * 10^6)", bg="black", fg="white").grid(
                    row=4, column=0, sticky="w"
                )
                Label(window, text="vy (m/s * 10^6)", bg="black", fg="white").grid(
                    row=5, column=0, sticky="w"
                )
                Label(window, text="Name", bg="black", fg="white").grid(
                    row=6, column=0, sticky="w"
                )
                Label(window, text="Material (list)", bg="black", fg="white").grid(
                    row=7, column=0, sticky="w"
                )

                Label(window, text="Not moving", bg="black", fg="white").grid(
                    row=8, column=0, sticky="w"
                )
                Label(window, text="Camera follow", bg="black", fg="white").grid(
                    row=9, column=0, sticky="w"
                )

                a1 = Entry(window)
                a1.grid(row=1, column=1)
                a1.insert(0, str(planet.x))

                b1 = Entry(window)
                b1.grid(row=2, column=1)
                b1.insert(0, str(planet.y))

                c1 = Entry(window)
                c1.grid(row=3, column=1)
                c1.insert(0, str(float(planet.r) / 10**6))

                d1 = Entry(window)
                d1.grid(row=4, column=1)
                d1.insert(0, str(planet.vx / 10**6))

                e1 = Entry(window)
                e1.grid(row=5, column=1)
                e1.insert(0, str(planet.vy / 10**6))

                f1 = Entry(window)
                f1.grid(row=6, column=1)
                f1.insert(0, planet.name)

                notmovingVar = IntVar(window)

                g1 = Checkbutton(
                    window,
                    text="Not moving ?",
                    variable=notmovingVar,
                    onvalue=1,
                    offvalue=0,
                )
                g1.grid(row=8, column=1)
                if planet.notmoving:
                    g1.select()

                camfollowVar = IntVar(window)

                h1 = Checkbutton(
                    window,
                    text="Camera follow ?",
                    variable=camfollowVar,
                    onvalue=1,
                    offvalue=0,
                )
                h1.grid(row=9, column=1)
                if planet.camfollow:
                    h1.select()

                material_choice = StringVar(window)
                material_choice.set(planet.material)

                OptionMenu(window, material_choice, *materials.keys()).grid(
                    row=7, column=1
                )
                Button(
                    window,
                    text="Edit",
                    command=lambda: addplanet(
                        a1.get(),
                        b1.get(),
                        c1.get(),
                        d1.get(),
                        e1.get(),
                        f1.get(),
                        material_choice,
                        window,
                        notmovingVar.get(),
                        camfollowVar.get(),
                        edited=clicked_planet,
                    ),
                ).grid(row=10, column=0)

                Button(
                    window,
                    text="Delete",
                    command=lambda: delete_planet(clicked_planet, window),
                ).grid(row=10, column=1)

                window.mainloop()
                # pour reset deltatime
                clock.tick(frames_per_second)

            # sinon en crée une nouvelle
            elif not planet_creating:
                # cree une nouvelle planete avec une fenetre tkinter
                planet_got_added = True
                pos = pygame.mouse.get_pos()
                window = tkinter.Tk()
                window.title("Add new planet")
                window.geometry("325x250")
                window.configure(background="Black")
                window.columnconfigure(0, weight=1)
                window.columnconfigure(1, weight=3)

                Label(
                    window,
                    text="Welcome to planet edition center !",
                    bg="black",
                    fg="white",
                ).grid(row=0, columnspan=3)

                Label(window, text="x coordinate", bg="black", fg="white").grid(
                    row=1, column=0, sticky="w"
                )
                Label(window, text="y coordinate", bg="black", fg="white").grid(
                    row=2, column=0, sticky="w"
                )
                Label(window, text="Ray (km^6)", bg="black", fg="white").grid(
                    row=3, column=0, sticky="w"
                )
                Label(window, text="vx (m/s * 10^6)", bg="black", fg="white").grid(
                    row=4, column=0, sticky="w"
                )
                Label(window, text="vy (m/s * 10^6)", bg="black", fg="white").grid(
                    row=5, column=0, sticky="w"
                )
                Label(window, text="Name", bg="black", fg="white").grid(
                    row=6, column=0, sticky="w"
                )
                Label(window, text="Material (list)", bg="black", fg="white").grid(
                    row=7, column=0, sticky="w"
                )

                Label(window, text="Not moving", bg="black", fg="white").grid(
                    row=8, column=0, sticky="w"
                )
                Label(window, text="Camera follow", bg="black", fg="white").grid(
                    row=9, column=0, sticky="w"
                )

                realX, realY = screen_to_real(pos[0], pos[1])

                a1 = Entry(window)
                a1.grid(row=1, column=1)
                a1.insert(0, str(realX))

                b1 = Entry(window)
                b1.grid(row=2, column=1)
                b1.insert(0, str(realY))

                c1 = Entry(window)
                c1.grid(row=3, column=1)
                d1 = Entry(window)
                d1.grid(row=4, column=1)
                e1 = Entry(window)
                e1.grid(row=5, column=1)
                f1 = Entry(window)
                f1.grid(row=6, column=1)
                notmovingVar = IntVar(window)

                g1 = Checkbutton(
                    window,
                    text="Not moving ?",
                    variable=notmovingVar,
                    onvalue=1,
                    offvalue=0,
                )
                g1.grid(row=8, column=1)

                camfollowVar = IntVar(window)

                h1 = Checkbutton(
                    window,
                    text="Camera follow ?",
                    variable=camfollowVar,
                    onvalue=1,
                    offvalue=0,
                )
                h1.grid(row=9, column=1)

                material_choice = StringVar(window)
                material_choice.set("none")
                OptionMenu(window, material_choice, *materials.keys()).grid(
                    row=7, column=1
                )
                Button(
                    window,
                    text="Create planet !",
                    command=lambda: addplanet(
                        a1.get(),
                        b1.get(),
                        c1.get(),
                        d1.get(),
                        e1.get(),
                        f1.get(),
                        material_choice,
                        window,
                        notmovingVar.get(),
                        camfollowVar.get(),
                    ),
                ).grid(row=10, column=0, columnspan=2)

                window.mainloop()
                # pour reset deltatime
                clock.tick(frames_per_second)

        # change l'echelle si on scroll
        if event.type == pygame.MOUSEBUTTONUP:
            scale_change_factor = 1.05
            if event.button == 5:
                change_scale(1 / scale_change_factor)
            elif event.button == 4:
                change_scale(scale_change_factor)

        # pour bouger la camera avec les fleches
        if event.type == pygame.KEYDOWN:
            keys = pygame.key.get_pressed()
            origin_change_factor = 5 / (scale.scale / original_scale)
            moved = False
            if keys[pygame.K_LEFT]:
                scale.changeCamOrigin(-origin_change_factor, 0)
                moved = True
            if keys[pygame.K_RIGHT]:
                scale.changeCamOrigin(origin_change_factor, 0)
                moved = True
            if keys[pygame.K_UP]:
                scale.changeCamOrigin(0, -origin_change_factor)
                moved = True
            if keys[pygame.K_DOWN]:
                scale.changeCamOrigin(0, origin_change_factor)
                moved = True

            # si on a bougé avec les fleches la camera on arrete de suivre les planetes avec la camera
            if moved:
                for planet in planets:
                    planet.camfollow = False


def thread1():

    pygame.init()
    # fps prédéfinis
    frames_per_second = 1000

    screen = pygame.display.set_mode((winDim.w, winDim.h))

    # régulateur automatique de fps
    clock = pygame.time.Clock()

    # commence en pause
    started = False
    planet_creating = False

    # charge des polices
    global littlefont
    littlefont = pygame.font.SysFont("Arial", 18)
    global bigfont
    bigfont = pygame.font.SysFont("Arial", 50)

    # background
    image_fond = pygame.image.load("fond.jpg")
    fond = image_fond.convert()
    fond = pygame.transform.scale(
        fond, (max(winDim.h, winDim.w), max(winDim.h, winDim.w))
    )

    global planet_got_added
    planet_got_added = False

    # load les images des textures
    for keyplanet in materials_filenames.keys():
        try:
            materials_files[keyplanet] = pygame.image.load(
                materials_filenames[keyplanet]
            )
        except:
            print(f"File {materials_filenames[keyplanet]} does not exist")

    # Joue la musique
    pygame.mixer.music.load("Space_song.mp3")
    pygame.mixer.music.play(-1)
    pygame.key.set_repeat(1, 10)

    while True:

        if not planet_got_added and not pause.paused:
            # la simulation se fait si elle n est pas en pause
            frame(clock, screen, fond, frames_per_second, started, planet_creating)
        else:
            frame(
                clock, screen, fond, frames_per_second, started, planet_creating, False
            )


# Prompt pour la taille de simulation
# si on ne choisi aucune taille de simulation, ca se fait automatiquement
sizeW = tkinter.Tk()
auto = tkinter.IntVar()
sizeW.title("Choose simulation size")
sizeW.geometry("300x100")
sizeW.configure(background="Black")
sizeW.columnconfigure(0, weight=1)
sizeW.columnconfigure(1, weight=3)

Label(
    sizeW,
    text="Choose a simulation size (nothing for automatic)",
    bg="black",
    fg="white",
).grid(row=0, columnspan=3)

Label(sizeW, text="width", bg="black", fg="white").grid(row=1, column=0, sticky="w")
Label(sizeW, text="Height", bg="black", fg="white").grid(row=2, column=0, sticky="w")

b1 = Entry(sizeW)
b1.grid(row=1, column=1)

d1 = Entry(sizeW)
d1.grid(row=2, column=1)
Button(sizeW, text="Ok !", command=lambda: setwinsize(b1, d1, sizeW)).grid(
    row=3, column=0, columnspan=2
)
sizeW.mainloop()
print(winDim.h)

# thread 1 = simulation
t1 = threading.Thread(target=thread1)
# thread 2 = pad de control (LCP)
t2 = threading.Thread(target=live_control_pad)

t1.start()
t2.start()