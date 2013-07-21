GimmickBuilder syntax
=====================

gimmicks.txt files are parsed as `YAML <http://www.yaml.org/>`_ documents, although GimmickBuilder only uses a fraction of the syntax of YAML. Comments are declared using a ``#`` (pound sign) and continue to the end of the line.

All gimmicks.txt files should be prefixed with a version declaration. This declaration is filled in automatically by the "Create gimmicks.txt skeleton" option::

    version: 0.2.0

From version 0.2 onward, there are two major blocks:

Definitions
-----------

Definitions describe gimmicks as BPM changes and stop values. Here is an example of a complete definition block::

    definitions:
        stutter:
            bpms:
                0: bpm * mul
            stops:
                0: 60 / (bpm * mul) * ((mul - 1) * len)
        halfbrake:
            bpms:
                0: bpm * mul
                0.5: bpm / ((mul - .5) * (2 / mul))

This definition block defines two gimmicks, *stutter* and *halfbrake*. These and a few other gimmicks are built into GimmickBuilder; they don't need to be (re-)defined in gimmicks.txt.

Each gimmick definition must have a *bpms* section and may have a *stops* section (colloquially, "timing sections"). Each timing section contains lines of the form "*position*: *value*", where *position* is a decimal number in the range [0..1) and *value* is a mathematical expression. *value* may reference certain variables: *bpm* is the song's current BPM, *mul* is the given multiplier, and *len* is the given length. (*mul* and *len* are described in further detail in the next section.)

Do not attempt to reset the BPM at the end of a gimmick, i.e. by setting the last line of the *bpms* block to ``1: bpm``. GimmickBuilder automatically resets the BPM when a gimmick has ended.

Built-in definitions
^^^^^^^^^^^^^^^^^^^^

* stutter: Multiplies the BPM by `mul` and inserts a stop at each interval to counteract the BPM increase.
* midstutter: Identical to `stutter`, but the stop is inserted halfway between each interval. Arguably easier for the player to read.
* halfbrake: Multiplies the BPM by `mul` for the first half, then decreases the BPM for the second half by exactly enough to counteract the first half.
* quarterbrake: Similar to `halfbrake`, but the BPM changes at the three-quarter mark, not the halfway mark.
* halfboost: Reverse of `halfbrake`.
* quarterboost: Reverse of `quarterbrake`.

Gimmicks
--------

The (admittedly poorly named) `gimmicks` section places gimmicks into the simfile as BPM changes and stops. Here is an example of a complete gimmick block::

    gimmicks:
        0: bpm 140
        8-16: 1/16 1.5x stutter
        16: bpm 70
        24: bpm 140
        31: 1/4 2x halfbrake
        32.5-33: 1/24 3x midstutter
        33-34: 1/16 1.5x mygimmick
        34-36: copy 32
        40: stop .5

There are four types of gimmick lines:

* BPM changes are defined as "*position*: bpm *bpm*". There must be a BPM change with a position of 0 at the beginning of the block.
* Stops are defined as "*position*: stop *len*". Note that *len* is measured in *beats*, not seconds, as .SM files represent stops.
* Normal gimmicks are defined as "*region*: *len* *mul* *definition*". *region* can be either "*start*" or "*start*-*end*"; in the former case, *end* is implicitly set to *start* + *len*. *len* is a fraction of a measure (not a beat!) that deterimines how quickly the gimmick will play and how frequently it will recur. *mul* is a decimal multiplier suffixed with an "x" that determines the intensity of a gimmick. When the distance from *start* to *end* is greater than *len* * 4, the gimmick will be played repeatedly until reaching the end of the region.
* Copy gimmicks are defined as "*start*-*end*: copy *source*". *source* is a beat from which to grab gimmicks that have already been parsed. The source's ending point is implicitly determined by the distance between *start* and *end*. The source and destination regions cannot overlap.

With this in mind, let's go through the example above line by line:

* ``0: bpm 140`` sets the simfile's initial BPM to 140.
* ``8-16: 1/16 1.5x stutter`` creates a stutter gimmick starting on beat 8 and ending on beat 16. There will be one stop on each 16th note and the BPM will be set to 140 × 1.5 = 210 throughout.
* ``16: bpm 70`` sets the BPM to 70 on beat 16.
* ``24: bpm 140`` sets the BPM back to 140 on beat 24.
* ``31: 1/4 2x halfbrake`` creates a single half-brake gimmick starting on beat 31 and lasting a quarter note (i.e. until beat 32), with an intensity of 2x.
* ``32.5-33: 1/24 3x midstutter`` creates a mid-stutter gimmick starting on beat 32.5 and ending on beat 33. There will be one stop between each 24th interval and the BPM will be set to 140 × 3 = 420 throughout.
* ``33-34: 1/16 1.5x mygimmick`` creates a gimmick defined by "mygimmick" between beats 33 and 34 with the given length and multiplier. "mygimmick" must have been declared in the `definitions` block of this gimmicks.txt file.
* ``34-36: copy 32`` takes the gimmicks from beats 32 through 34 and duplicates them into beats 34 through 36.
* ``40: stop .5`` creates a stop on beat 40 that lasts half a beat.

Limitations
-----------

* Gimmicks cannot intersect one another, although a gimmick can immediately follow the previous gimmick (e.g. a gimmick on 24-32 followed by another on 32-40).
* Right now there is no way to have two gimmick lines on the same beat (e.g. a BPM change and a stop on the same beat). Attempting to do this results in the second gimmick line being omitted. This is a limitation of the underlying YAML parser; it will hopefully have a workaround by version 0.3.
* The behavior of a copy gimmick whose source region's current BPM and destination region's current BPM are different is undefined. (I haven't tried it yet but it probably isn't pretty.)