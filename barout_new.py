#!/usr/bin/python
# -*- coding: utf-8 -*- 
import subprocess, time, sys, pywapi, traceback, os, signal, select, procname

def fitwidth(count, lstr, cstr, rstr):
	lsep = count/2 - len(lstr) - len(cstr)/2

	rem = count - lsep - len(cstr) - len(lstr) - len(rstr)

	return (lstr + 
			lsep * u" " + 
			cstr + 
			rem * u" " + 
			rstr)

def genbatteryh(width, percent):
	return u"["+"".join([
		u"•" # c_horizontal_bar((percent - float(i)/width) * 10) 
			if (i< width * percent) 
			else u" "
		for i in range(width)
		])+u"]"

def c_horizontal_bar(p):
	return (u"▏" if (p<1.0/8) else
			u"▎" if (p<2.0/8) else
			u"▍" if (p<3.0/8) else
			u"▌" if (p<4.0/8) else
			u"▋" if (p<5.0/8) else
			u"▊" if (p<6.0/8) else
			u"▉" if (p<7.0/8) else
			u"█")

def c_vertical_bar(p):
	return (u"▁" if (p<1.0/8) else
			u"▂" if (p<2.0/8) else
			u"▃" if (p<3.0/8) else
			u"▄" if (p<4.0/8) else
			u"▅" if (p<5.0/8) else
			u"▆" if (p<6.0/8) else
			u"▇" if (p<7.0/8) else
			u"█")

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
	chars = [
		(u" \u2b92" if state[0] == "Charging"
		else u" \u2b90" if state[0] == "Discharging"
		else u"??") +
		genbatteryh(10,state[1]) +
		str(int (100 * state[1])) +
		"% (" + state[2] + ")"

		for state in bstate]

	return u"\u00A0".join(chars)

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


def bspwmDesktopState():
	desktops = bspwmDesktops()
	active = bspwmActiveDesktop()

	return	"".join([ u"❤" if (d == active) else u"•" for d in desktops])

def do_printout():
		try:
			battstr = makebstr(battery())
			datestr = time.strftime(u"%a %b %d, %Y")
			timestr = time.strftime(u"%I:%M %p")

			al = alevel() #audio
			bl = blevel() #battery
			
			astr = u"\u2B9F %2i"%(al*100) #(c_vertical_bar(al) if al != 0 else "/")
			bstr = u"\u2BA6 %2i"%(bl*100) #c_vertical_bar(bl)
			
			print fitwidth (
				screenlen,
				astr + u"" + bstr + u"" + bspwmDesktopState(), 
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


screenlen = 155;
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

