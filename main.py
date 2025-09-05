import sqlite3
import datetime
import math
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.patches import Patch
import os
from PIL import Image
import numpy as np

script_dir = os.path.dirname(__file__)

# If you happen to have SF Symbol images as files, map the symbol name here:
# sf_images['house.fill'] = '/path/to/house.fill.png'
# sf_images['person.3.fill'] = '/path/to/person.3.fill.png'
sf_images = {}
sf_images['house.fill'] = os.path.join(script_dir, 'icons', 'house.png')
sf_images['person.3.fill'] = os.path.join(script_dir, 'icons', 'user.png')
sf_images['guitars.fill'] = os.path.join(script_dir, 'icons', 'music.png')
sf_images['fork.knife'] = os.path.join(script_dir, 'icons', 'slice.png')
sf_images['building.fill'] = os.path.join(script_dir, 'icons', 'building-office.png')
sf_images['rectangle.fill.on.rectangle.angled.fill'] = os.path.join(script_dir, 'icons', 'square-stack.png')
sf_images['cart.fill'] = os.path.join(script_dir, 'icons', 'cart.png')
sf_images['shoeprints.fill'] = os.path.join(script_dir, 'icons', 'globe-alt.png')
sf_images['building.columns.fill'] = os.path.join(script_dir, 'icons', 'building-library.png')
sf_images['moon.fill'] = os.path.join(script_dir, 'icons', 'moon.png')
# credit to https://heroicons.com/solid and https://remixicon.com/

avg_sleep_hours = 7.5

swift_epoch = datetime.datetime(2001, 1, 1, tzinfo=datetime.timezone.utc)
now_utc = datetime.datetime.now(datetime.timezone.utc)
delta = now_utc - swift_epoch
lookback_time = float(input('Look back how many days? '))
selected_departure = delta - datetime.timedelta(days=lookback_time)

types = [['gray', 'question', 'Uncategorized'], ['gray', 'question', 'Uncategorized'], ['green', 'walk', 'Walking'], ['green', 'run', 'Running'], ['green', 'bike', 'Cycling'], ['brown', 'car.fill', 'Motor Vehicle'], ['cyan', 'plane', 'Flight']]

show_home = int(input("Would you like to include HOME? (0/1) "))
show_work = int(input("Would you like to include WORK? (0/1) "))
if show_home == 1:
    include_time_sleeping = int(input("Would you like to REMOVE TIME SLEEPING from time at HOME? (0/1) "))
    if include_time_sleeping == 1:
        include_sleep = int(input("Would you like to SHOW TIME SLEEPING in the GRAPH? (0/1) "))
    else:
        include_sleep = 0
else:
    include_time_sleeping = 0
    include_sleep = 0
merge_transport = int(input("What would you like to do with TRANSPORT (0 - include individual, 1 - include merged, 2 - do not include) "))

with sqlite3.connect('LifeEasy.sqlite') as conn:
    zvisit = conn.cursor()
    zvisit.execute('SELECT ZACTIVITY_, ZLOCATION, ZARRIVALDATE_, ZDEPARTUREDATE_ FROM ZVISIT where ZDEPARTUREDATE_ > ?', (selected_departure.total_seconds(), ))
    visits = zvisit.fetchall()

    zlocation = conn.cursor()
    zlocation.execute('SELECT Z_PK, ZUSERIGNORED, ZLATITUDE, ZLONGITUDE, ZADMINISTRATIVEAREA, ZRADIUS, ZNAME_, ZTIMEZONE FROM ZLOCATION')
    locations = zlocation.fetchall()

    zactivity = conn.cursor()
    zactivity.execute('SELECT Z_PK, ZISHOME, ZISWORK, ZCOLOR_, ZICON_, ZNAME_ FROM ZACTIVITY')
    activities = zactivity.fetchall()

    zmovement = conn.cursor()
    zmovement.execute('SELECT ZTYPE_, ZTRANSPORT_, ZVISITFROM_, ZVISITTO_, ZSTART_, ZEND_ FROM ZMOVEMENT where ZEND_ > ?', (selected_departure.total_seconds(), )) # type is built in modes, transport is custom modes
    movements = zmovement.fetchall() # types is currently hardcoded in the types dict above

    ztransport = conn.cursor()
    ztransport.execute('SELECT Z_PK, ZCOLOR_, ZICON_, ZNAME_ FROM ZTRANSPORT')
    transports = ztransport.fetchall()

loc_by_id = { loc_id: loc_rec for (loc_id, *loc_rec) in locations }
act_by_id = { act_id: act_rec for (act_id, *act_rec) in activities }
tra_by_id = { tra_id: tra_rec for (tra_id, *tra_rec) in transports }

visit_set = []
for activity_id, location_id, *rest in visits:
    location = loc_by_id.get(location_id)
    activity = act_by_id.get(activity_id)
    if location and activity:
        visit_set.append((list((activity_id, location_id, *rest)), location, activity))

movement_set = []
for type_id, transport_id, *rest in movements:
    type = types[type_id]
    if type[2] == 'Motor Vehicle':
        transport = tra_by_id.get(transport_id)
    else:
        transport = types[type_id]
    if transport == None:
        transport = types[1]
    if type:
        movement_set.append((list((*rest, )), transport))

'''
print(movement_set)
print(visit_set)
for visit in visit_set:
    if visit[1][0] == 2: # visits not marked ignored
        arrival_date = visit[0][2]
        departure_date = visit[0][3]
        lat = visit[1][1]
        long = visit[1][2]
        administrative_area = visit[1][3]
        radius = visit[1][4]
        name = visit[1][5]
        is_home = visit[2][0]
        is_work = visit[2][1]
        color = visit[2][2]
        icon_id = visit[2][3]
        activity_name = visit[2][4]
        # timezone = visit[1][6]
print(selected_departure.total_seconds())
'''

durations, colors, icons = {}, {}, {}
for meta, place, act in visit_set:
    if place[0] != 0: continue
    is_home, is_work = bool(act[0]), bool(act[1])
    if (is_home and show_home == 0) or (is_work and show_work == 0):
        continue

    duration = meta[3] - meta[2]
    activity = act[4]
    durations[activity] = durations.get(activity, 0) + duration
    colors[activity]    = act[2]
    icons[activity]     = act[3]

if merge_transport == 0:
    for data, act in movement_set:
        duration = data[3] - data[2]
        activity = act[2]
        durations[activity] = durations.get(activity, 0) + duration
        colors[activity]    = act[0]
        icons[activity]     = act[1]
elif merge_transport == 1:
    colors["Transport"] = types[5][0]
    icons["Transport"]  = types[5][1]
    for data, act in movement_set:
        duration = data[3] - data[2]
        durations["Transport"] = durations.get("Transport", 0) + duration



if not durations:
    print("Nothing to plot."); exit()

if include_time_sleeping == 1:
    home_duration = durations.get('Home', 0)
    if home_duration >= avg_sleep_hours*3600*lookback_time:
        durations['Home'] -= avg_sleep_hours*3600*lookback_time
        if include_sleep == 1:
            if 'Sleep' not in durations:
                colors['Sleep'] = 'black'
                icons['Sleep'] = 'moon.fill'
            durations['Sleep'] = durations.get('Sleep', 0) + avg_sleep_hours*3600*lookback_time

labels = list(durations)
sizes  = [durations[a] for a in labels]
cols   = [colors[a]    for a in labels]

fig, ax = plt.subplots(figsize=(6,6))
wedges, _ = ax.pie(
    sizes,
    colors=cols,
    startangle=90,
    wedgeprops=dict(width=0.5)
)
ax.axis('equal')

# Label each wedge with text or icon
for w, activity in zip(wedges, labels):
    # mid‐angle
    ang = (w.theta2 + w.theta1) / 2
    # position at 70% of the wedge radius
    r = getattr(w, 'r', 1)  # default r=1
    x = r * 0.7 * math.cos(math.radians(ang))
    y = r * 0.7 * math.sin(math.radians(ang))

    if icons[activity] in sf_images:
        pil_img = Image.open(sf_images[icons[activity]])
        if pil_img.mode != 'RGBA':
            pil_img = pil_img.convert('RGBA')
        img_data = np.asarray(pil_img).astype(np.float32) / 255.0
        fig_size = fig.get_size_inches()
        base_size = min(fig_size[0], fig_size[1])
        wedge_angle = w.theta2 - w.theta1
        wedge_proportion = wedge_angle / 360.0
        dynamic_zoom = 0.15 * (base_size / 6.0) * max(0.5, min(2.0, wedge_proportion * 10))
        im = OffsetImage(img_data, zoom=dynamic_zoom)
        ab = AnnotationBbox(im, (x, y), frameon=False)
        ax.add_artist(ab)
        pil_img.close()
    else:
        ax.text(x, y, activity,
                ha='center', va='center',
                fontsize=10, color='white', weight='bold')

# Legend
entries = []
for activity in labels:
    patch = Patch(facecolor=colors[activity], edgecolor='k', lw=0.5)
    entries.append((patch, f"{activity}"))

patches, texts = zip(*entries)
ax.legend(patches, texts,
          title="Activity",
          bbox_to_anchor=(1.0, 0.5),
          loc="center left")

plt.tight_layout()
plt.show()
