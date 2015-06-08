#!/usr/bin/python
# -*- coding: utf-8 -*- 
import subprocess, time, sys, pywapi, traceback
import os, signal, select, procname, toml

with open(os.path.expanduser("~/.mbarrc")) as conffile:
        config = toml.loads(conffile.read())

def fitwidth(count, lstr, cstr, rstr):
	lsep = count/2 - len(lstr) - len(cstr)/2

	rem = count - lsep - len(cstr) - len(lstr) - len(rstr)

	return (lstr + 
			lsep * u" " + 
			cstr + 
			rem * u" " + 
			rstr)

battery_ends = {
	"up": u"\u2593",
	"down": u"\u2592",
	"neither": u"\u2591",
}
def genbatteryh(width, percent, direction="neither"):
	return battery_ends[direction] + "".join([
			genbatterys((percent - float(i)/width) * 10) if (i< width * percent) else
			u"\u2597"
			for i in range(width)
		])+u"\u2590" # custom right battery

def genbatterys(p):
	return (u"\u259F" if (p<1.0/8) else
			u"\u259E" if (p<2.0/8) else
			u"\u259D" if (p<3.0/8) else
			u"\u259C" if (p<4.0/8) else
			u"\u259B" if (p<5.0/8) else
			u"\u259A" if (p<6.0/8) else
			u"\u2599" if (p<7.0/8) else
			u"\u2598")

def genbatteryv(p):
	return (u"\u25b0" if (p<1.0/8) else
			u"\u25b1" if (p<2.0/8) else
			u"\u25b2" if (p<3.0/8) else
			u"\u25b3" if (p<4.0/8) else
			u"\u25b4" if (p<5.0/8) else
			u"\u25b5" if (p<6.0/8) else
			u"\u25b6" if (p<7.0/8) else
			u"\u25b7")

def getperc(line):
	spl = line.split(",")
	state = spl[0].split(":")[1].strip();
	percent = float(spl[1].replace("%", ""))/100.0

	try:
		time = spl[2].replace(" remaining", "").strip()
	except:
		time = ":full"

	return (
		state, 
		percent, 
		":".join(time.split(":")[0:2])
	)

def battery():
	p = subprocess.Popen(
		["acpi"], 
		stdout=subprocess.PIPE)
	out = p.communicate()[0]

	return [
		getperc(line)
		for line in out.split("\n") if line != ""
	]

def alevel():
	p = subprocess.Popen(
		["amixer"], 
		stdout=subprocess.PIPE)
	out = p.communicate()[0]

	for line in out.split("\n"):
		if line.endswith("[on]"):
			s = line.split("[")[1].split("%")[0]
			return float(s)/100
		elif line.endswith("[off]"):
			return 0

	return 0

def blevel():
	p = subprocess.Popen(
		["xbacklight"], 
		stdout=subprocess.PIPE)
	out = p.communicate()[0]

	return 	float(out)/100

def wlevel():
	return 0

def makebstr(bstate):
	chars = []
	for state in bstate:
		direction = ("up" if state[0] == "Charging"
			else "down" if state[0] == "Discharging"
			else "neither")

		chars+= [
			genbatteryh(8, state[1], direction) +
			str(int (100 * state[1])) +
			"% (" + state[2] + ")"
		]

	return u" ".join(chars)

lastweather = 0
wIcon = u"?"
wTemp = u"??°C"
def getWeatherMemoized():
	global lastweather, wTemp, wIcon
	#update hourly
	if (time.time() - lastweather > 60 * 60):
		lastweather = time.time()
		wres = pywapi.get_weather_from_yahoo('10001')
		wTemp = (wres['condition']['temp'] + u"°C"
			#+ wres['condition']['text']
		)

		#print wres

		cond = wres['condition']['text']
		if cond == u"Sunny":
			wIcon = u"⛭"
		elif cond == u"Mostly Sunny":
			wIcon = u"⛯"
		elif cond == u"Fair":
			wIcon = u"⚙"
		elif cond == u"Partly Cloudy":
			wIcon = u"⛅"
		elif cond == u"Cloudy":
			wIcon = u"☁"
		elif cond == u"Raining":
			wIcon = u"☔" #☂
		elif cond == u"Snowing":
			wIcon = u"⛄"
		else:
			wIcon = u"☭"

def bspwmDesktops():
	p = subprocess.Popen(
		["bspc","query","-D"], 
		stdout=subprocess.PIPE)
	out = p.communicate()[0]
	return out.split("\n")[:-1]


def bspwmActiveDesktop():
	p = subprocess.Popen(
		["bspc", "query","-d", "focused","-D"], 
		stdout=subprocess.PIPE)
	out = p.communicate()[0]
	return out.replace("\n", "")


desktop_descriptors = (config["desktop_descriptors"] 
        if config and config["desktop_descriptors"] 
        else {
        	"I": "work",
	        "II": "libs",
	        "III": "chat",
	        "IIX": "gimp"
        })
def bspwmDesktopState():
	desktops = bspwmDesktops()
	active = bspwmActiveDesktop()

	indicator = "".join([ u"\u26ab" if (d == active) else u"\u8226" for d in desktops])
	descriptor = (" ("+desktop_descriptors[active]+")"
		if active in desktop_descriptors.keys()
		else u"")

	return indicator + descriptor

def do_printout():
		try:
			battstr = makebstr(battery())
			datestr = time.strftime(u"%a %b %d, %Y")
			timestr = time.strftime(u"%I:%M %p")

			al = alevel() #audio
			bl = blevel() #battery
			wl = wlevel() #wireless

			astr = "v" + (genbatteryv(al) if al != 0 else u"/")
			bstr = "b" + genbatteryv(bl)

			print fitwidth (
				screenlen,
				astr + u" " + bstr + u" " + bspwmDesktopState(), 
				datestr + " (" + timestr + ")", 
				battstr).encode('utf-8');

			sys.stdout.flush()

			#getWeatherMemoized()

		except Exception as e:
			print fitwidth (
				screenlen,
				"",
				str(e),
				"").encode('utf-8')
			sys.stdout.flush()
			#print traceback.format_exc()


screenlen = 168;
#screenlen = 90;
if __name__ == "__main__":
	# open up listener fd
	procname.setprocname('mybar')

	pipe_read, pipe_write = os.pipe()

	signal.set_wakeup_fd(pipe_write)

	# Set up a signal to repeat every 1/3rd of a second
	fps = 1
	signal.setitimer(signal.ITIMER_REAL, fps, fps)
	signal.signal(signal.SIGALRM, lambda x,y: None)
	signal.signal(signal.SIGIOT, lambda x,y: None)

	poller = select.epoll()
	poller.register(pipe_read, select.EPOLLIN)


	while True:
		try:
			events = poller.poll()
			os.read(pipe_read, 1);

			do_printout()
		except IOError, OSError:
			pass

