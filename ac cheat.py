from ReadWriteMemory import ReadWriteMemory
from tkinter import *
from tkinter import ttk
import math
import struct
import win32api


rwm = ReadWriteMemory()
process = rwm.get_process_by_name('ac_client.exe')
process.open()

game_address = 0x00400000 #Unused
local_player_address = 0x00587C0C
player_array = 0x00587C10
player_count = 0x00587C18

position_offsets = [0x04, 0x08, 0x0C] #Unused
camera_offsets = [0x34, 0x38] #Unused

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

master = Tk()
master.overrideredirect(1)
master.attributes('-topmost', True)
master.wm_attributes('-transparentcolor', '#ab23ff')
canvas = Canvas(master, width=200, height=200)

def aim(yaw, pitch):
    yaw_pointer = process.get_pointer(local_player_address, offsets=[0x34])
    pitch_pointer = process.get_pointer(local_player_address, offsets=[0x38])
    
    converted_yaw = struct.unpack("<I", struct.pack("<f", yaw))
    converted_pitch = struct.unpack("<I", struct.pack("<f", pitch))
    
    process.write(yaw_pointer, converted_yaw[0])
    process.write(pitch_pointer, converted_pitch[0])

def get_vector_between_player(localpos=False, enemypos=False, toggle_aim=False):
    if localpos == False:
        localpos = local_player.position()
        
    if enemypos == False:
        enemypos = get_all_player_positions()[0]
        
    x_diff = enemypos[0] - localpos[0]
    y_diff = enemypos[1] - localpos[1]
    z_diff = enemypos[2] - localpos[2]
    
    dist = math.sqrt(z_diff * z_diff + x_diff * x_diff)
    pitch = math.atan2(y_diff, dist) *  180.0 / math.pi
    yaw =  math.atan2(x_diff / dist, z_diff / dist) * 180 / math.pi
    yaw = abs(yaw - 180)
    
    if toggle_aim:
        aim(yaw, pitch)
    else:
        return yaw

def get_closest_enemy(aim=False):
    positions = get_all_player_positions()
    player_yaw = process.read(process.get_pointer(local_player_address, offsets=[0x34]), True)
    lowest = [0, 360]
    for i, x in enumerate(positions): 
        difference = abs(player_yaw - get_vector_between_player(enemypos=x))
        if difference < lowest[1] and x[3] != local_player.team() and x[4] > 0 and x[4] < 101: 
            lowest[0] = i
            lowest[1] = abs(player_yaw - get_vector_between_player(enemypos=x))
            
    if positions[lowest[0]][3] != local_player.team():
        get_vector_between_player(enemypos=positions[lowest[0]], toggle_aim=True)
        
    

def draw_radar():
    while True:
        if win32api.GetAsyncKeyState(ord('Q')) != 0:
            get_closest_enemy(True)
            
        positions = get_all_player_positions()
        if positions == []: pass
        localpos = local_player.position()
        yaw = math.radians(local_player.yaw())
        if local_player.health() > 0 and local_player.health() < 101:
            entity = canvas.create_rectangle(15, 15, 0, 0, fill="green") 
            canvas.move(entity, 100, 100)
            
        for pos in positions:  
            if(pos[3] == local_player.team()):
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