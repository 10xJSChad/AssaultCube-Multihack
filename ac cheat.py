from ReadWriteMemory import ReadWriteMemory
from tkinter import *
from tkinter import ttk
import math
import struct
import win32api
import win32con
import ctypes
import random
import time
import threading

rwm = ReadWriteMemory()
process = rwm.get_process_by_name('ac_client.exe')
process.open()

game_address = 0x00400000 #Unused
local_player_address = 0x00587C0C
gamemode_address = 0x0059FC11
player_array = 0x00587C10
player_count = 0x00587C18

position_offsets = [0x04, 0x08, 0x0C] #Unused
camera_offsets = [0x34, 0x38] #Unused

speedhack_value = 3
aim_assist_fov = 5
aim_assist_enabled = True
aim_assist_speed = 0.05
radar_enabled = True
in_menu = False

class local_player():
    def health():
        return(process.read(process.get_pointer(local_player_address, offsets=[0xEC])))
        
    def position():
        x = process.read(process.get_pointer(local_player_address, offsets=[0x04]), True)
        z = process.read(process.get_pointer(local_player_address, offsets=[0x08]), True)
        y = process.read(process.get_pointer(local_player_address, offsets=[0xC]), True)
        return([x, y, z])
    
    def yaw():
        x = process.read(process.get_pointer(local_player_address, offsets=[0x34]), True)
        return(x)
    
    def team():
        team_value = process.read(process.get_pointer(local_player_address, offsets=[0x30C]))
        return(team_value)
    
def pointer_loop(array, start=0, stop=10, read=False):
    i = 0
    result = []
    for j in range(start, stop):
        i += 4
        if read:
            result.append(process.read(process.get_pointer(array, offsets=[hex(i)])))
        else:
            result.append(process.get_pointer(array, offsets=[hex(i)]))
    return result
    
def get_all_players():
    return(pointer_loop(player_array, 1, process.read(player_count)))
    
def get_all_player_positions(float=True):
    players = get_all_players()
    result = []
    for player in players:
        x = process.read(process.get_pointer(player, offsets=[0x04]), float)
        z = process.read(process.get_pointer(player, offsets=[0x08]), float)
        y = process.read(process.get_pointer(player, offsets=[0xC]), float)
        team = process.read(process.get_pointer(player, offsets=[0x30C]))
        health = process.read(process.get_pointer(player, offsets=[0xEC]))
        result.append([x, y, z, team, health])
    return result

player_test = process.get_pointer(player_array, offsets=[0x08, 0xEC])

def menu():
    global speedhack_value, aim_assist_enabled, aim_assist_fov, radar_enabled, aim_assist_speed
    top = Tk()   
    top.geometry("350x130") 
    top.overrideredirect(1)
    top.attributes('-topmost', True)
    top.geometry('+0+200')
    
    speed_text = StringVar()
    speed_text.set("Speedhack: 3")
    speed_label = Label(top, 
                    textvariable=speed_text, font=("Courier", 18)).place(x=0, y=0)
    
    aimassist_toggle_text = StringVar()
    aimassist_toggle_text.set("Aim Assist: ON")
    aimassist_toggle_label = Label(top, 
                    textvariable=aimassist_toggle_text, font=("Courier", 18)).place(x=0, y=25)
    
    aimassist_text = StringVar()
    aimassist_text.set("Aim Assist FOV: 5")
    aimassist_label = Label(top, 
                    textvariable=aimassist_text, font=("Courier", 18)).place(x=0, y=50)
    
    aimassist_speed_text = StringVar()
    aimassist_speed_text.set("Radar: ON")
    aimassist_speed_label = Label(top, 
                    textvariable=aimassist_speed_text, font=("Courier", 18)).place(x=0, y=75)
    
    radar_toggle_text = StringVar()
    radar_toggle_text.set("Radar: ON")
    radar_label = Label(top, 
                    textvariable=radar_toggle_text, font=("Courier", 18)).place(x=0, y=100)
    
    text_objects = [speed_text, aimassist_toggle_text, aimassist_text, aimassist_speed_text, radar_toggle_text]
    
    selected = -0
    while True:
        text = ["Speedhack: " + str(speedhack_value), "Aim Assist: " + str(aim_assist_enabled), "Aim Assist FOV: " + str(aim_assist_fov), "Aim Assist Speed: " + str(aim_assist_speed), "Radar: " + str(radar_enabled)]
        
        for i in range(0, len(text_objects)):
            if i != selected:
                text_objects[i].set(text[i])
            else:
                text_objects[selected].set(text[selected] + " <---")
        
        if win32api.GetAsyncKeyState(win32con.VK_UP) != 0: 
            time.sleep(0.1)
            if selected > 0: 
                selected -= 1
            text_objects[selected].set(text[selected] + " <---")
            
        if win32api.GetAsyncKeyState(win32con.VK_DOWN) != 0: 
            time.sleep(0.1)
            if selected < len(text_objects) - 1: 
                selected += 1
            text_objects[selected].set(text[selected] + " <---")
            
        if win32api.GetAsyncKeyState(win32con.VK_RIGHT) != 0: 
            time.sleep(0.1)
            if selected == 0: speedhack_value += 1
            if selected == 1: aim_assist_enabled = not aim_assist_enabled
            if selected == 2: aim_assist_fov += 1
            if selected == 3: aim_assist_speed += 0.01
            if selected == 4: radar_enabled = not radar_enabled
            
        if win32api.GetAsyncKeyState(win32con.VK_LEFT) != 0: 
            time.sleep(0.1)
            if selected == 0: speedhack_value -= 1
            if selected == 1: aim_assist_enabled = not aim_assist_enabled
            if selected == 2: aim_assist_fov -= 1
            if selected == 3: aim_assist_speed -= 0.01
            if selected == 4: radar_enabled = not radar_enabled
            
        if win32api.GetAsyncKeyState(ord('M')) != 0:
            time.sleep(0.1)
            top.destroy()
            draw_radar()
            
        top.update() 


def is_teammate(target):
    current_gamemode = process.read(gamemode_address)
    if current_gamemode == 539118916 or current_gamemode == 575489090: 
        return False
    if target[3] == local_player.team():
        return True
    else:
        return False
    
def aim(yaw, pitch):
    yaw_pointer = process.get_pointer(local_player_address, offsets=[0x34])
    pitch_pointer = process.get_pointer(local_player_address, offsets=[0x38])
    
    converted_yaw = struct.unpack("<I", struct.pack("<f", yaw))
    converted_pitch = struct.unpack("<I", struct.pack("<f", pitch))
    
    process.write(yaw_pointer, converted_yaw[0])
    process.write(pitch_pointer, converted_pitch[0])

def aim_assist(yaw_and_pitch):
    yaw_target = yaw_and_pitch[0]
    pitch_target = yaw_and_pitch[1]
    
    yaw_pointer = process.get_pointer(local_player_address, offsets=[0x34])
    pitch_pointer = process.get_pointer(local_player_address, offsets=[0x38])
    
    player_yaw = process.read(yaw_pointer, True)
    player_pitch = process.read(pitch_pointer, True)
    
    if int(player_yaw) > int(yaw_target):
        converted_yaw = struct.unpack("<I", struct.pack("<f", player_yaw - aim_assist_speed))
        process.write(yaw_pointer, converted_yaw[0])
    elif int(player_yaw) < int(yaw_target):
        converted_yaw = struct.unpack("<I", struct.pack("<f", player_yaw + aim_assist_speed))
        process.write(yaw_pointer, converted_yaw[0])
        
    if int(player_pitch) > int(pitch_target):
        converted_pitch = struct.unpack("<I", struct.pack("<f", player_pitch - aim_assist_speed))
        process.write(pitch_pointer, converted_pitch[0])
    elif int(player_pitch) < int(pitch_target):
        converted_pitch = struct.unpack("<I", struct.pack("<f", player_pitch + aim_assist_speed))
        process.write(pitch_pointer, converted_pitch[0])
    
def get_vector_between_player(localpos=False, enemypos=False, toggle_aim=False):
    if localpos == False:
        localpos = local_player.position()
        
    if enemypos == False:
        enemypos = get_all_player_positions()
        if enemypos != []:
            enemypos = enemypos[0]
        
    x_diff = enemypos[0] - localpos[0]
    y_diff = enemypos[1] - localpos[1]
    z_diff = enemypos[2] - localpos[2]
    
    
    dist = math.sqrt(z_diff * z_diff + x_diff * x_diff)
    pitch = math.atan2(y_diff, dist) *  180.0 / math.pi
    
    if dist > 0.0:
        yaw =  math.atan2(x_diff / dist, z_diff / dist) * 180 / math.pi
        yaw = abs(yaw - 180)
    else:
        yaw = 0
    
    if toggle_aim:
        aim(yaw, pitch)
    else:
        return (yaw, pitch)

def get_closest_enemy(aimbot=False, aimassist=False):
    positions = get_all_player_positions()
    if positions == []: return
    
    player_yaw = process.read(process.get_pointer(local_player_address, offsets=[0x34]), True)
    player_pitch = process.read(process.get_pointer(local_player_address, offsets=[0x38]), True)
    lowest = [0, 360, 360]
    for i, x in enumerate(positions): 
        difference = abs(player_yaw - get_vector_between_player(enemypos=x)[0])
        if difference < lowest[1] and not is_teammate(x) and x[4] > 0 and x[4] < 101: 
            lowest[0] = i
            lowest[1] = abs(player_yaw - get_vector_between_player(enemypos=x)[0])
            lowest[2] = abs(player_pitch - get_vector_between_player(enemypos=x)[1])
            
    if not is_teammate(positions[lowest[0]]) and (positions[lowest[0]][4] > 0 and positions[lowest[0]][4] < 101):
        if aimbot:
            get_vector_between_player(enemypos=positions[lowest[0]], toggle_aim=True)
        if aimassist and lowest[1] < aim_assist_fov and lowest[2] < aim_assist_fov:
            aim_assist(get_vector_between_player(enemypos=positions[lowest[0]]))
        return(positions[lowest[0]])
        
 
telekill_target_index = None
def telekill():
    global telekill_target_index
    positions = get_all_player_positions()
    if positions == []: return
    
    if telekill_target_index == None:
        telekill_target_index = random.randint(0, len(positions)-1)
        return
    else:
        telekill_target = positions[telekill_target_index]
        
    if is_teammate(telekill_target) or telekill_target[4] < 0 or telekill_target[4] > 100:
        telekill_target_index = None
        return

    x_pointer = process.get_pointer(local_player_address, offsets=[0x04])
    y_pointer = process.get_pointer(local_player_address, offsets=[0x08])
    z_pointer = process.get_pointer(local_player_address, offsets=[0x0C])
     
    converted_enemy_x = struct.unpack("<I", struct.pack("<f", telekill_target[0]))
    converted_enemy_y = struct.unpack("<I", struct.pack("<f", telekill_target[2]))
    converted_enemy_z = struct.unpack("<I", struct.pack("<f", telekill_target[1]))
    
    process.write(x_pointer, converted_enemy_x[0])
    process.write(y_pointer, converted_enemy_y[0])
    process.write(z_pointer, converted_enemy_z[0])
    
    ctypes.windll.user32.mouse_event(2, 0, 0, 0,0)
    
def speedhack():
    speed_pointer = process.get_pointer(local_player_address, offsets=[0x74])
    process.write(speed_pointer, speedhack_value)
    
       
def draw_radar():
    global in_menu
    master = Tk()
    master.overrideredirect(1)
    master.attributes('-topmost', True)
    master.wm_attributes("-transparentcolor", "white")
    canvas = Canvas(master, width=200, height=200)
    
    if not radar_enabled:
        master.geometry('+0-5000')
    
    while True:
        if aim_assist_enabled:
            get_closest_enemy(aimassist=True)
            
        if win32api.GetAsyncKeyState(ord('Q')) != 0:
            get_closest_enemy(True)
            
        if win32api.GetAsyncKeyState(ord('H')) != 0:
            telekill()
            
        if win32api.GetAsyncKeyState(ord('C')) != 0:
            speedhack()
            
        if win32api.GetAsyncKeyState(ord('M')) != 0:
            time.sleep(0.1)
            master.destroy()
            menu()
            
        positions = get_all_player_positions()
        if positions == []: pass
        localpos = local_player.position()
        yaw = math.radians(local_player.yaw())
        if local_player.health() > 0 and local_player.health() < 101:
            entity = canvas.create_rectangle(15, 15, 0, 0, fill="green") 
            canvas.move(entity, 100, 100)
            
        for pos in positions:  
            if(is_teammate(pos)):
                color = "blue"
            else:
                color = "red"    
            
            if pos[4] > 0 and pos[4] < 101:
                entity = canvas.create_rectangle(15, 15, 0, 0, fill=color) 
                x = pos[0] - localpos[0]
                z = pos[2] - localpos[2]
                
                x_transform = x * math.cos(-yaw) - z * math.sin(-yaw)
                z_transform = x * math.sin(-yaw) + z * math.cos(-yaw)
                
                canvas.move(entity, (x_transform + 100), (z_transform + 100))
        canvas.pack()
        master.update()
        canvas.delete("all")
        
draw_radar()