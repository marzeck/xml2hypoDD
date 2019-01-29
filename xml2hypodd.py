#!/usr/bin/env python

import datetime
from pyrocko.io import stationxml
from pyrocko.io import quakeml

def stationXML2stationDD(filename, output='station.dat'):
	'''
	Write the station.data input file for ph2dt and hypodd.
	The input format is stationXML.

	:param filename: string or list of strings
	:param output: string of output-filename

	returns output
	'''

	if isinstance(filename, str):
		inv = stationxml.load_xml(filename=filename)
	elif isinstance(filename, list):
		inv = stationxml.load_xml(filename=filename[0])
		for fi in filename[1:]:
			inv.network_list.extend(stationxml.load_xml(filename=fi).network_list)

	outStat = []
	for netStat in inv.ns_code_list:
		s = [stat for stat in inv.get_pyrocko_stations() if netStat[0] == stat.network and netStat[1] == stat.station][0]
		outStat.append(
			' '.join(map(str, [netStat[0] + netStat[1], s.lat, s.lon, '\n'])))

	with open(output, 'w') as f:
		f.writelines(outStat)

	return(output)


def quakeml2phaseDD(filename, output='phase.dat', convID=True, confirmed=True):
	'''
	Write the phase.dat input file for ph2dt and hypodd.
	The input format is quakeML.

	:param filename: string or list of strings
	:param output: string of output-filename
	:param convID: bool, whether to save a file with IDs to link quakeML
		public_id with hypoDD eventID
	:param confirmed: bool, if True only picks with evaluation_status confirmed are used
	'''

	if isinstance(filename, str):
		qmlIn = quakeml.QuakeML.load_xml(filename=filename)
	elif isinstance(filename, list):
		qmlIn = quakeml.QuakeML.load_xml(filename=filename)
		for fi in filename[1:]:
			qmlIn.event_parameters.event_list.extend(
				quakeml.QuakeML.load_xml(filename=fi).event_parameters.event_list)

	iD = 1
	eventString = []
	if convID:
		conv = []
	for event in qmlIn.event_parameters.event_list:
		if not event.preferred_origin:
			raise quakeml.NoPreferredOriginSet()
		else:
			orig = event.preferred_origin
		ti = datetime.datetime.utcfromtimestamp(orig.time.value)
		try:
			mag = event.preferred_magnitude.mag.value
		except AttributeError:
			continue
		try:
			EH = float(orig.origin_uncertainty_list[0].max_horizontal_uncertainty)/1000
		except:
			EH = 0.0
		try:
			EZ = float(orig.depth.uncertainty)/1000
		except:
			EZ = 0.0
		try:
			RMS = orig.quality.standard_error
			if RMS is None:
				RMS = 0.0
		except AttributeError:
			RMS = 0.0

		string = "# {year} {month} {day} {hour} {minute} " + \
			"{second} {latitude} {longitude} " + \
			"{depth} {magnitude:.2f} {horizontal_error} " + \
			"{depth_error} {rms} {event_id:>9.9}\n"

		eventString.append(string.format(
			year=ti.year,
			month=ti.month,
			day=ti.day,
			hour=ti.hour,
			minute=ti.minute,
			second=float(ti.second) + (ti.microsecond / 1e6),
			latitude=orig.latitude.value,
			longitude=orig.longitude.value,
			depth=orig.depth.value / 1000,
			magnitude=mag,
			horizontal_error=EH,
			depth_error=EZ,
			rms=RMS,
			event_id=str(iD)))

		stringList = []
		for pick in event.pick_list:
			if pick.evaluation_status != 'confirmed' and confirmed:
				continue
			string = "{station_id:7s} {travel_time:.6f} {weight:.2f} {phase}\n"
			pickString = string.format(
				station_id=(
					pick.waveform_id.network_code +
					pick.waveform_id.station_code),
				travel_time=(
					pick.time.value -
					event.preferred_origin.time.value),
				weight=1,
				phase=pick.phase_hint.value[0])
			if pickString not in stringList:
				stringList.append(pickString)
				eventString.append(pickString)

		iD += 1
		if convID:
			conv.append((str(iD) + ';' + str(event.public_id) + '\n'))

	with open(output,'w') as f:
		f.writelines(eventString)

	if convID:
		with open('convIDs.txt','w') as g:
			g.writelines(conv)


def relocDD2quakeml(dd_reloc, output_file, dd_loc=None, input_file=None, convID=None, phases=None):
	'''
	Converts hypoDD output file into into quakeML format.
	Either input_file or dd_loc must be given!
	When using old quakeML data, convID file must be given
	:param dd_reloc: string, name of hypoDD output file with relocated events
	:param dd_loc: string, name of hypoDD file with starting locations
	:param input_file: string, name of quakeML file for input  to hypoDD
	:param convID: string, file with IDs to link quakeML public_id with hypoDD eventID
	'''

	# check parameter dependencies
	if not dd_loc and not input_file:
		raise quakeml.QuakeMLError('Either dd_loc or input_file must be given!')

	if convID and not input_file:
		raise quakeml.QuakeMLError('When convID given, a quakeml file must be given to input_file!')

	if input_file and not convID:
		raise quakeml.QuakeMLError('When input_file given, a convID must be given!')

	with open(dd_reloc, 'r') as f:
		relocated = [line.split() for line in f.read().splitlines()]

	# load quakeml
	# or initial locations and convert them to quakeML
	if input_file is not None:
		qmlDD = quakeml.QuakeML.load_xml(filename=input_file)
		with open(convID, 'r') as f:
			conversion = [tuple(line.split(';')) for line in f.read().splitlines()]
	else:
		with open(dd_loc, 'r') as f:
			initial = [line.split() for line in f.read().splitlines()]

		if phases is not None:
			with open(phases, 'r') as f:
				phaseList = [line.splitlines() for line in f.read().split('#')[1:]]

		eventList = []
		for ev in initial:
			evAbsTime = datetime.datetime(
				year=int(ev[10]),
				month=int(ev[11]),
				day=int(ev[12]),
				hour=int(ev[13]),
				minute=int(ev[14]),
				second=int(ev[15].split('.')[0]),
				microsecond=int(ev[15].split('.')[1])*1000)
			evTimestamp = (evAbsTime - datetime.datetime(1970,1,1)).total_seconds()
			pickList = []
			for bloc in phaseList:
				if ev[0] == bloc[0].split()[-1]:
					for phase in bloc[1:]:
						pickList.append(quakeml.Pick(
							public_id='smi:relocDD/pick/P-{0}-{1}'.format(
								evTimestamp +phase.split()[1],
								phase.split()[0],
								len(pickList)),
							time=quakeml.TimeQuantity(
								value=(evTimestamp + phase.split()[1])),
							waveform_id=quakeml.WaveformStreamID(
								network_code=phase.split()[0][0:2],
								station_code=phase.split()[0][2:]),
							phase_hint=quakeml.Phase(value=phase.split()[3])))
			origUncert = quakeml.OriginUncertainty(
				max_horizontal_uncertainty=max(
					float(ev[7]),
					float(ev[8])),
				min_horizontal_uncertainty=min(
					float(ev[7]),
					float(ev[8])),
				preferred_description='horizontal uncertainty')
			origin = quakeml.Origin(
				public_id='smi:relocDD/origin/O-{0}-{1}-init'.format(ev[0], evTimestamp),
				origin_uncertainty_list=[origUncert],
				time=quakeml.TimeQuantity(value=evTimestamp),
				longitude=quakeml.RealQuantity(value=float(ev[2])),
				latitude=quakeml.RealQuantity(value=float(ev[1])),
				depth=quakeml.RealQuantity(
					value=float(ev[3]),
					uncertainty=float(ev[9])),
				type='hypocenter',
				evaluation_mode='automatic',
				evaluation_status='preliminary')
			magnitude = quakeml.Magnitude(
				public_id='smi:relocDD/magnitude/M-{0}-{1}'.format(ev[0], evTimestamp),
				mag=quakeml.RealQuantity(value=float(ev[16])))
			eventList.append(quakeml.Event(
				public_id='smi:relocDD/event/E-{0}-{1}'.format(ev[0], evTimestamp),
				magnitude_list=[magnitude],
				origin_list=[origin],
				pick_list=pickList,
				preferred_origin_id=origin.public_id,
				preferred_magnitude_id=magnitude.public_id,
				type='earthquake',
				type_certainty='known'))

		qmlDD = quakeml.QuakeML(event_parameters=quakeml.EventParameters(
			public_id='smi:relocDD/catalog/C-{0}'.format(
				(datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds()),
			event_list=eventList))

	# add relocated hypocenters to catalog
	for reloc in relocated:
		evAbsTime = datetime.datetime(
			year=int(reloc[10]),
			month=int(reloc[11]),
			day=int(reloc[12]),
			hour=int(reloc[13]),
			minute=int(reloc[14]),
			second=int(reloc[15].split('.')[0]),
			microsecond=int(reloc[15].split('.')[1])*1000)
		evTimestamp = (evAbsTime - datetime.datetime(1970,1,1)).total_seconds()
		origUncert = quakeml.OriginUncertainty(
			max_horizontal_uncertainty=max(
				float(reloc[7]),
				float(reloc[8])),
			min_horizontal_uncertainty=min(
				float(reloc[7]),
				float(reloc[8])),
			preferred_description='horizontal uncertainty')
		origin = quakeml.Origin(
			public_id='smi:relocDD/origin/O-{0}-{1}-reloc'.format(reloc[0], evTimestamp),
			origin_uncertainty_list=[origUncert],
			time=quakeml.TimeQuantity(value=evTimestamp),
			longitude=quakeml.RealQuantity(value=float(reloc[2])),
			latitude=quakeml.RealQuantity(value=float(reloc[1])),
			depth=quakeml.RealQuantity(
				value=float(reloc[3]),
				uncertainty=float(reloc[9])),
			quality=quakeml.OriginQuality(standard_error=float(reloc[22])),
			type='hypocenter',
			evaluation_mode='automatic',
			evaluation_status='preliminary')

		if convID:
			pubID = [conv[1] for conv in conversion if conv[0] == reloc[0]][0]
		else:
			pubID = [ev.public_id for ev in qmlDD.event_parameters.event_list if 'E-' + reloc[0] + '-' in ev.public_id][0]

		for event in qmlDD.event_parameters.event_list:
			if event.public_id == pubID:
				event.origin_list.append(origin)
				event.preferred_origin_id = origin.public_id

	# store quakeml catalog
	qmlDD.dump_xml(filename=output_file)
