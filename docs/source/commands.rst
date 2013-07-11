Built-in commands
=================

Five commands are currently bundled with synctools.

AdjustOffset
------------

Adds a fixed amount to the OFFSET value.

This command (among others) uses Python's :py:class:`Decimal` class to avoid floating-point precision loss.

ClickTrack
----------

Generates a file named "clicktrack.wav" in the same directory as the .sm file.

The clicks are synchronized to the simfile's BPM changes and stops. The click track can contain three types of "clicks": a noise channel "metronome" on each quarter note, a sine bloop on each tap note, and a square bloop on each mine / bomb. The taps and mines are loaded from a chart that is determined primarily by difficulty (Challenge, then Hard, Medium, Easy, Beginner, and Edit), secondarily by game type (dance, then pump, then ez2), and tertiarily by game mode (single, then double). This usually means the dance-single Expert chart. If no suitable charts are found, it uses the first chart in the simfile.

A global offset can also be added to the click track. This is useful for syncing charts to hardware with a known global offset or other delay, such as In The Groove 2 cabinets, which have a global offset of -0.012 and a sonic delay of 3 milliseconds for a final offset of -0.009.

FixStops
--------

Mitigates the effects of imprecise rounding in stop values.

StepMania truncates stop values after three decimal places (one millisecond). Charts that make heavy use of stops will more often than not drift noticeably offsync after awhile. This command keeps track of the imprecisions and strategically adds or removes milliseconds to compensate for the lack of precision.

To figure out the "intended" duration of each stop, FixStops uses the BPM at the time of the stop and assumes it's aligned to a 192nd note. This means it generally won't work if the chart author tried to fix the offset values by hand, but stops created by the StepMania editor's "Convert selection to stop" feature will always be correctable.

GimmickBuilder
--------------

Converts a gimmicks.txt file in the same directory as the .sm file into BPM changes and stops.

Syntax details are forthcoming.

Patch
-----

Applies a length patch to OGG files.

In The Groove 2 revison 21 enables players to load custom simfiles from their USB drives, but prohibits songs longer than two minutes. However, this check is only done once when loading the OGG file. "Patching" the actual length of the audio file to a value under two minutes circumvents this restriction.