# encoding: utf-8

###########################################################################################################
#
#
#	File Format Plugin
#	Implementation for exporting fonts through the Export dialog
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/File%20Format
#
#	For help on the use of Interface Builder:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates
#
#
###########################################################################################################

from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
import codecs
from os import path

@objc.python_method
def saveFileInLocation(content="", fileName="font.ps", filePath="~/Desktop"):
	saveFileLocation = "%s/%s" % (filePath, fileName)
	saveFileLocation = saveFileLocation.replace( "//", "/" )
	content=codecs.encode(content, encoding='utf-8')
	content=codecs.decode(content, encoding='ascii', errors='ignore')
	with codecs.open(saveFileLocation, "w", encoding="ascii", errors="ignore") as thisFile:
		# print("Exporting PS:", thisFile.name) # DEBUG
		thisFile.write(content)
		thisFile.close()
	return True

class PSExport(FileFormatPlugin):
	prefDomain = "com.mekkablue.ExportPostScript"
	prefDict = {
		"removeOverlap": True,
		"outline": True,
		"onlyShapes": True,
		"metricsMarkers": False,
	}
	
	# Definitions of IBOutlets
	# The NSView object from the User Interface. Keep this here!
	dialog = objc.IBOutlet()
	checkboxRemoveOverlap = objc.IBOutlet()
	checkboxOutline = objc.IBOutlet()
	checkboxOnlyShapes = objc.IBOutlet()
	checkboxMetricsMarkers = objc.IBOutlet()

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			'en': 'PS Export',
			'de': 'PostScript-Export',
			})
		self.icon = 'ExportIcon'
		self.toolbarPosition = 100
		
		# Load .nib dialog (with .extension)
		self.loadNib('IBdialog', __file__)
		
	@objc.python_method
	def start(self):
		# Init user preferences if not existent and set default value
		for prefKey in self.prefDict.keys():
			domain = "%s.%s" % (self.prefDomain, prefKey)
			Glyphs.registerDefault(domain, self.prefDict[prefKey])
			getattr(self, "checkbox"+prefKey[0].upper()+prefKey[1:]).setState_(Glyphs.defaults[domain])
	
	@objc.IBAction
	def setOutline_(self, sender):
		Glyphs.defaults[self.prefDomain+".outline"] = bool(sender.intValue())
	
	@objc.IBAction
	def setRemoveOverlap_(self, sender):
		Glyphs.defaults[self.prefDomain+".removeOverlap"] = bool(sender.intValue())

	@objc.IBAction
	def setOnlyShapes_(self, sender):
		Glyphs.defaults[self.prefDomain+".onlyShapes"] = bool(sender.intValue())

	@objc.IBAction
	def setMetricsMarkers_(self, sender):
		Glyphs.defaults[self.prefDomain+".metricsMarkers"] = bool(sender.intValue())

	@objc.python_method
	def layerToPS(self, thisLayer, comment, markerSize=30):
		charstring = ""
		if comment:
			charstring += "%%%% %s\n" % comment
		for p in thisLayer.paths:
			# charstring += "newpath\n"
			n = p.nodes[-1]
			charstring += "%i %i moveto\n" % (n.x, n.y)
			iscurve=False
			for n in p.nodes[:-1]:
				if n.type==LINE:
					charstring += "%i %i lineto\n" % (n.x, n.y)
					iscurve=False
				elif n.type==OFFCURVE:
					charstring += "%i %i " % (n.x, n.y)
					iscurve=True
				elif n.type==CURVE:
					charstring += "%i %i curveto\n" % (n.x, n.y)
					iscurve=False
			if iscurve:
				n=p.nodes[-1]
				charstring += "%i %i curveto\n" % (n.x, n.y)
			charstring += "closepath\n"
		if Glyphs.defaults[self.prefDomain+".outline"]:
			charstring += "stroke"
		else:
			charstring += "fill"
		if Glyphs.defaults[self.prefDomain+".metricsMarkers"]:
			charstring += "\n-%i 0 moveto 0 0 lineto " % (markerSize)
			charstring += "0 %i moveto 0 -%i lineto " % (markerSize, markerSize)
			charstring += "%i 0 moveto %i 0 lineto " % (thisLayer.width, thisLayer.width+markerSize)
			charstring += "%i %i moveto %i -%i lineto " % (thisLayer.width, markerSize, thisLayer.width, markerSize)
			charstring += "stroke\n"
		charstring += "\nshowpage\n\n"
		return charstring

	@objc.python_method
	def export(self, font):
		# Ask for export destination and write the file:
		title = "Choose export destination"
		exportFolder = GetFolder(message=title, allowsMultipleSelection=False, path=None)
		onlyShapes = Glyphs.defaults[self.prefDomain+".onlyShapes"]
		removeOverlap = Glyphs.defaults[self.prefDomain+".removeOverlap"]
		
		if exportFolder:
			count = 0
			for thisInstance in [i for i in font.instances if i.active and i.type==INSTANCETYPESINGLE]:
				count += 1
				psContent = "%!PS\n<</Install { 100 300 translate .4 .4 scale } bind >> setpagedevice\n\n"
				interpolatedFont = thisInstance.interpolatedFont
				for thisGlyph in [g for g in interpolatedFont.glyphs if g.export]:
					thisLayer = thisGlyph.layers[0].copyDecomposedLayer()
					if thisLayer.shapes or not onlyShapes:
						if removeOverlap:
							thisLayer.removeOverlap()
						psContent += self.layerToPS(thisLayer, thisGlyph.name)
				# psContent += "%% "

				saveFileInLocation(
					content=psContent,
					fileName="%s.ps" % thisInstance.fileName().stringByDeletingDotSuffix(),
					filePath=exportFolder,
					)
			
			return (True, '%i PS file%s exported in ???%s???.' % (count, "" if count==1 else "s", path.basename(exportFolder)))
		else:
			return (False, 'No folder chosen.')

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
