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
def saveFileInLocation(content="", fileName="glyph.eps", filePath="~/Desktop"):
	saveFileLocation = "%s/%s" % (filePath, fileName)
	saveFileLocation = saveFileLocation.replace( "//", "/" )
	content=codecs.encode(content, encoding='utf-8')
	content=codecs.decode(content, encoding='ascii', errors='ignore')
	with codecs.open(saveFileLocation, "w", encoding="ascii", errors="ignore") as thisFile:
		thisFile.write(content)
		thisFile.close()
	return True

class EPSExport(FileFormatPlugin):
	prefDomain = "com.mekkablue.EPSExport"
	prefDict = {
		"removeOverlap": True,
		"outline": True,
		"onlyShapes": True,
		"metricsMarkers": False,
		"selectedGlyphsOnly": False,
	}
	
	# Definitions of IBOutlets
	# The NSView object from the User Interface. Keep this here!
	dialog = objc.IBOutlet()
	checkboxRemoveOverlap = objc.IBOutlet()
	checkboxOutline = objc.IBOutlet()
	checkboxOnlyShapes = objc.IBOutlet()
	checkboxMetricsMarkers = objc.IBOutlet()
	checkboxSelectedGlyphsOnly = objc.IBOutlet()

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			'en': 'EPS Export',
			'de': 'EPS-Export',
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
			checkboxName = "checkbox"+prefKey[0].upper()+prefKey[1:]
			print(prefKey, checkboxName)
			getattr(self, checkboxName).setState_(Glyphs.defaults[domain])
	
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

	@objc.IBAction
	def setSelectedGlyphsOnly_(self, sender):
		Glyphs.defaults[self.prefDomain+".selectedGlyphsOnly"] = bool(sender.intValue())

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
		selectedGlyphsOnly = Glyphs.defaults[self.prefDomain+".selectedGlyphsOnly"]
		
		if exportFolder:
			count = 0
			for thisInstance in [i for i in font.instances if i.active and i.type==INSTANCETYPESINGLE]:
				instanceFileName = thisInstance.fileName().stringByDeletingDotSuffix()
				
				interpolatedFont = thisInstance.interpolatedFont
				for thisGlyph in [g for g in interpolatedFont.glyphs if g.export and (g in font.selection or not selectedGlyphsOnly)]:
					thisLayer = thisGlyph.layers[0].copyDecomposedLayer()
					if thisLayer.shapes or not onlyShapes:
						epsContent = "%!PS-Adobe-3.1 EPSF-3.0\n"
						epsContent += "%%BoundingBox: %i %i %i %i\n" % (
							thisLayer.bounds.origin.x-30,
							thisLayer.bounds.origin.y-30,
							thisLayer.bounds.origin.x+thisLayer.bounds.size.width+30,
							thisLayer.bounds.origin.y+thisLayer.bounds.size.height+30,
							)
						if removeOverlap:
							thisLayer.removeOverlap()
						epsContent += self.layerToPS(thisLayer, thisGlyph.name)
						saveFileInLocation(
							content=epsContent,
							fileName="%s-%s.eps" % (instanceFileName, thisGlyph.name),
							filePath=exportFolder,
							)
						count += 1
			
			return (True, '%i EPS file%s exported in ‘%s’.' % (count, "" if count==1 else "s", path.basename(exportFolder)))
		else:
			return (False, 'No folder chosen.')

	@objc.python_method
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
