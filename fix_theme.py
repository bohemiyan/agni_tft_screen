import json

with open(r'c:\Users\Chirag\Desktop\agni_tft_screen\s1panel\themes\agni_dark\agni_dark.json', 'r') as f:
    j = json.load(f)

screen4 = next(s for s in j['screens'] if s['id'] == 4)

for w in screen4['widgets']:
    wid = w['id']
    val = w.get('value','')

    # cpu_temp only has {0}=degrees, {1}=history, {2}=unit
    if wid == 17 and val == 'cpu_temp':
        w['format'] = 'TEMP  {0}{2}'

    # widget 18 clock format
    if wid == 18 and val == 'clock':
        w['format'] = '{1} {3}'

    # power label widget 9
    if wid == 9 and val == 'cpu_power':
        w['format'] = 'PWR  {0} W'

    print(f'  w{wid} value={val!r} format={w["format"]!r}')

with open(r'c:\Users\Chirag\Desktop\agni_tft_screen\s1panel\themes\agni_dark\agni_dark.json', 'w') as f:
    json.dump(j, f, indent=3)

print('Done - fixed screen 4 format strings')
