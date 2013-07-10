#!/usr/bin/env python
import os
import shutil
import struct
import zlib

from synctools import command

__all__ = ['Patch']

# Taken from mutagen/_util.py
bitswap = ''.join([chr(sum([((val >> i) & 1) << (7-i) for i in range(8)]))
    for val in range(256)])

class Patch(command.SynctoolsCommand):
    
    title = 'Length-patch OGG'
    description = 'trick In The Groove r21 into accepting long songs'
    fields = [
        {
            'name': 'length',
            'title': 'Patched length in seconds',
            'input': command.FieldInputs.text,
            'default': 105,
            'type': command.FieldTypes.between(0, 600),
        },
        {
            'name': 'backup_audio',
            'title': 'Backup audio file?',
            'input': command.FieldInputs.boolean,
            'default': True,
            'type': command.FieldTypes.yesno,
        },
    ]
    
    def run(self, simfile):
        super(Patch, self).run(simfile)
        
        # Get audio path
        ogg = os.path.join(os.path.dirname(simfile.filename), simfile['MUSIC'])
        if not os.path.splitext(ogg)[1].lower() == '.ogg':
            self.log.error('Only OGG is supported')
            return
        
        # Backup audio
        if self.options['backup_audio']:
            shutil.copy2(ogg, ogg + '~')
        
        # Get audio data
        with open(ogg, 'rb') as audiofile:
            audiodata = audiofile.read()
        
        # Find last page by the 4-byte header + version 0 + last page indicator
        lpindex = audiodata.rfind('OggS\x00')
        if lpindex == -1:
            self.log.error('Unable to find last OGG page')
            return
        if not ord(audiodata[lpindex + 5]) & 4:
            self.log.error('There is something very wrong with this OGG')
            return
        lp = audiodata[lpindex:]
        
        # TODO: don't assume 44.1kHz below
        # Get original length & insert new length
        patchlength = self.options['length']
        oldlength = struct.unpack('<q', lp[6:14])[0]
        oldlength /= 44100.
        lp = lp[:6] + struct.pack('<q', patchlength * 44100) + lp[14:]
        
        # Insert new CRC sum
        # Note: Python computes CRC backwards relative to OGG
        crc = (~zlib.crc32((lp[:22] + '\x00' * 4 + lp[26:]).translate(bitswap), 
            -1)) & 0xffffffff
        lp = (lp[:22] + struct.pack('>I', crc).translate(bitswap) + lp[26:])
        
        # Write new audio file
        with open(ogg, 'wb') as audiofile:
            audiofile.write(audiodata[:lpindex])
            audiofile.write(lp)
        self.log.info('Patched audio length from %s seconds to %s seconds' %
            (oldlength, patchlength))