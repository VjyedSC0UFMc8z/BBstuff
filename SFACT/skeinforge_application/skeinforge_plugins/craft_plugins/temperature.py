"""
This page is in the table of contents.
Temperature is a script to set the temperature for the object and raft.

==Operation==
The default 'Activate Temperature' checkbox is on.  When it is on, the functions described below will work, when it is off, the functions will not be called.

==Settings==
===Rate===
The default cooling rate and heating rate for the extruder were both been derived from bothacker's graph at:
http://bothacker.com/wp-content/uploads/2009/09/18h5m53s9.29.2009.png

====Cooling Rate====
Default is three degrees Celcius per second.

Defines the cooling rate of the extruder.

====Heating Rate====
Default is ten degrees Celcius per second.

Defines the heating rate of the extruder.

===Temperature===
====Base Temperature====
Default for ABS is two hundred degrees Celcius.

Defines the raft base temperature.

====Interface Temperature====
Default for ABS is two hundred degrees Celcius.

Defines the raft interface temperature.

====Object First Layer Infill Temperature====
Default for ABS is 195 degrees Celcius.

Defines the infill temperature of the first layer of the object.

====Object First Layer Perimeter Temperature====
Default for ABS is two hundred and twenty degrees Celcius.

Defines the perimeter temperature of the first layer of the object.

====Object Next Layers Temperature====
Default for ABS is two hundred and thirty degrees Celcius.

Defines the temperature of the next layers of the object.

====Support Layers Temperature====
Default for ABS is two hundred degrees Celcius.

Defines the support layers temperature.

====Supported Layers Temperature====
Default for ABS is two hundred and thirty degrees Celcius.

Defines the temperature of the supported layers of the object, those layers which are right above a support layer.

==Examples==
The following examples add temperature information to the file Screw Holder Bottom.stl.  The examples are run in a terminal in the folder which contains Screw Holder Bottom.stl and temperature.py.

> python temperature.py
This brings up the temperature dialog.

> python temperature.py Screw Holder Bottom.stl
The temperature tool is parsing the file:
Screw Holder Bottom.stl
..
The temperature tool has created the file:
.. Screw Holder Bottom_temperature.gcode

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from fabmetheus_utilities.fabmetheus_tools import fabmetheus_interpret
from fabmetheus_utilities import archive
from fabmetheus_utilities import euclidean
from fabmetheus_utilities import gcodec
from fabmetheus_utilities import intercircle
from fabmetheus_utilities import settings
from skeinforge_application.skeinforge_utilities import skeinforge_craft
from skeinforge_application.skeinforge_utilities import skeinforge_polyfile
from skeinforge_application.skeinforge_utilities import skeinforge_profile
import math
import sys


__author__ = 'Enrique Perez (perez_enrique@yahoo.com) modifed as SFACT by Ahmet Cem Turan (ahmetcemturan@gmail.com)'
__date__ = '$Date: 2008/21/04 $'
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'


def getCraftedText( fileName, text='', repository=None):
	"Temperature the file or text."
	return getCraftedTextFromText(archive.getTextIfEmpty(fileName, text), repository)

def getCraftedTextFromText(gcodeText, repository=None):
	"Temperature a gcode linear move text."
	if gcodec.isProcedureDoneOrFileIsEmpty( gcodeText, 'temperature'):
		return gcodeText
	if repository == None:
		repository = settings.getReadRepository( TemperatureRepository() )
	if not repository.activateTemperature.value:
		return gcodeText
	return TemperatureSkein().getCraftedGcode(gcodeText, repository)

def getNewRepository():
	'Get new repository.'
	return TemperatureRepository()

def writeOutput(fileName, shouldAnalyze=True):
	"Temperature a gcode linear move file."
	skeinforge_craft.writeChainTextWithNounMessage(fileName, 'temperature', shouldAnalyze)


class TemperatureRepository:
	"A class to handle the temperature settings."
	def __init__(self):
		"Set the default settings, execute title & settings fileName."
		skeinforge_profile.addListsToCraftTypeRepository('skeinforge_application.skeinforge_plugins.craft_plugins.temperature.html', self )
		self.fileNameInput = settings.FileNameInput().getFromFileName( fabmetheus_interpret.getGNUTranslatorGcodeFileTypeTuples(), 'Open File for Temperature', self, '')
		self.activateTemperature = settings.BooleanSetting().getFromValue('Activate Temperature:', self, False )
		settings.LabelSeparator().getFromRepository(self)
		settings.LabelDisplay().getFromName('- Rate -', self )
		self.coolingRate = settings.IntSpin().getFromValue( 1, 'Cooling Rate (Celcius/second):', self, 200, 100)
		self.heatingRate = settings.IntSpin().getFromValue( 1, 'Heating Rate (Celcius/second):', self, 200, 100 )
		settings.LabelSeparator().getFromRepository(self)
		settings.LabelDisplay().getFromName('- Temperature - Defaults are for PLA', self )
		self.baseTemperature = settings.IntSpin().getFromValue( 150, 'Base Temperature (Celcius):', self, 240, 210 )
		self.interfaceTemperature = settings.IntSpin().getFromValue( 150, 'Interface Temperature (Celcius):', self, 240, 210 )
		self.objectFirstLayerInfillTemperature = settings.IntSpin().getFromValue( 150, 'Object First Layer Infill Temperature (Celcius):', self, 240, 210 )
		self.objectFirstLayerPerimeterTemperature = settings.IntSpin().getFromValue( 150, 'Object First Layer Perimeter Temperature (Celcius):', self, 240, 210 )
		self.objectNextLayersTemperature = settings.IntSpin().getFromValue( 150, 'Object Next Layers Temperature (Celcius):', self, 240, 210 )
		self.supportLayersTemperature = settings.IntSpin().getFromValue( 150, 'Support Layers Temperature (Celcius):', self, 240, 210 )
		self.supportedLayersTemperature = settings.IntSpin().getFromValue( 150, 'Supported Layers Temperature (Celcius):', self, 240, 210 )
		self.executeTitle = 'Temperature'

	def execute(self):
		"Temperature button has been clicked."
		fileNames = skeinforge_polyfile.getFileOrDirectoryTypesUnmodifiedGcode(self.fileNameInput.value, fabmetheus_interpret.getImportPluginFileNames(), self.fileNameInput.wasCancelled)
		for fileName in fileNames:
			writeOutput(fileName)


class TemperatureSkein:
	"A class to temperature a skein of extrusions."
	def __init__(self):
		self.distanceFeedRate = gcodec.DistanceFeedRate()
		self.lineIndex = 0
		self.lines = None

	def getCraftedGcode(self, gcodeText, repository):
		"Parse gcode text and store the temperature gcode."
		self.repository = repository
		self.lines = archive.getTextLines(gcodeText)
		if self.repository.coolingRate.value < 0.1:
			print('The cooling rate should be more than 0.1, any cooling rate less than 0.1 will be treated as 0.1.')
			self.repository.coolingRate.value = 0.1
		if self.repository.heatingRate.value < 0.1:
			print('The heating rate should be more than 0.1, any heating rate less than 0.1 will be treated as 0.1.')
			self.repository.heatingRate.value = 0.1
		self.parseInitialization()
		self.distanceFeedRate.addLines( self.lines[self.lineIndex :] )
		return self.distanceFeedRate.output.getvalue()

	def parseInitialization(self):
		'Parse gcode initialization and store the parameters.'
		for self.lineIndex in xrange(len(self.lines)):
			line = self.lines[self.lineIndex]
			splitLine = gcodec.getSplitLineBeforeBracketSemicolon(line)
			firstWord = gcodec.getFirstWord(splitLine)
			self.distanceFeedRate.parseSplitLine(firstWord, splitLine)
			if firstWord == '(</extruderInitialization>)':
				self.distanceFeedRate.addLine('(<procedureName> temperature </procedureName>)')
				return
			elif firstWord == '(<perimeterWidth>':
				self.distanceFeedRate.addTagBracketedLine('coolingRate', self.repository.coolingRate.value )
				self.distanceFeedRate.addTagBracketedLine('heatingRate', self.repository.heatingRate.value )
				self.distanceFeedRate.addTagBracketedLine('baseTemperature', self.repository.baseTemperature.value )
				self.distanceFeedRate.addTagBracketedLine('interfaceTemperature', self.repository.interfaceTemperature.value )
				self.distanceFeedRate.addTagBracketedLine('objectFirstLayerInfillTemperature', self.repository.objectFirstLayerInfillTemperature.value )
				self.distanceFeedRate.addTagBracketedLine('objectFirstLayerPerimeterTemperature', self.repository.objectFirstLayerPerimeterTemperature.value )
				self.distanceFeedRate.addTagBracketedLine('objectNextLayersTemperature', self.repository.objectNextLayersTemperature.value )
				self.distanceFeedRate.addTagBracketedLine('supportLayersTemperature', self.repository.supportLayersTemperature.value )
				self.distanceFeedRate.addTagBracketedLine('supportedLayersTemperature', self.repository.supportedLayersTemperature.value )
			self.distanceFeedRate.addLine(line)


def main():
	"Display the temperature dialog."
	if len(sys.argv) > 1:
		writeOutput(' '.join(sys.argv[1 :]))
	else:
		settings.startMainLoopFromConstructor(getNewRepository())

if __name__ == "__main__":
	main()
