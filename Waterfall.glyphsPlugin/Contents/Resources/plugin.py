# encoding: utf-8

###########################################################################################################
#
#
#	General Plugin
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/General%20Plugin
#
#
###########################################################################################################


#https://developer.apple.com/library/content/documentation/Cocoa/Conceptual/CocoaViewsGuide/SubclassingNSView/SubclassingNSView.html

from GlyphsApp import *
from GlyphsApp.plugins import *
from vanilla import *
from AppKit import NSAffineTransform, NSRectFill, NSView, NSNoBorder, NSColor, NSBezierPath, NSMutableParagraphStyle, NSParagraphStyleAttributeName
from Foundation import NSWidth, NSHeight, NSMidX, NSMidY
import traceback
import re

surrogate_pairs = re.compile(u'[\ud800-\udbff][\udc00-\udfff]', re.UNICODE)
surrogate_start = re.compile(u'[\ud800-\udbff]', re.UNICODE)
emoji_variation_selector = re.compile(u'[\ufe00-\ufe0f]', re.UNICODE)


class WaterfallView(NSView):
	
	def glyphForName(self, name, font):
		if len(name) == 1:
			glyph_unicode = "%.4X" % ord(name)
		else:
			glyph_unicode = name.encode('unicode-escape')
		glyph = font.glyphs[glyph_unicode]
		if glyph is None:
			if len(glyph_unicode) == 10:
				glyph_unicode = glyph_unicode[5:].upper()
			glyph = f.glyphForUnicode_(glyph_unicode)
		if glyph is None:
			glyph = font.glyphs['.notdef']
		return glyph
		
	def drawRect_(self, rect):
		self.wrapper._backColour.set()
		NSBezierPath.fillRect_(rect)
		sizes = [8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 24, 28, 32, 36, 48, 60, 72, 90, 120]
		lineSpace = 8
		tab = 30
		w = NSWidth(self.frame())
		h = NSHeight(self.frame())
		glyphNames = self.wrapper._glyphsList
		insIndex = self.wrapper._instanceIndex
		if insIndex == 0:
			font = Glyphs.font
			m = font.selectedFontMaster
		else:
			instance = Glyphs.font.instances[insIndex-1]
			font = self.wrapper.instances.get(instance.name)
			if font is None:
				font = instance.interpolatedFont
				self.wrapper.instances[instance.name] = font
			m = font.masters[0]
		fullPath = NSBezierPath.alloc().init()
		advance = 0
		self.wrapper._foreColour.set()
		
		try:
			for i, glyphName in enumerate(glyphNames):
				
				glyph = self.glyphForName(glyphName, font)
				if glyph:
					layer = glyph.layers[m.id]
					
					layerPath = layer.completeBezierPath
					kernValue = 0
					# kerning check
					if i+1 < len(glyphNames):
						nextGlyphName = glyphNames[i+1]
						nextGlyph = self.glyphForName(nextGlyphName, font)
						if nextGlyph:
							nextLayer = nextGlyph.layers[m.id]
							if nextLayer:
								kernValue = layer.rightKerningForLayer_(nextLayer)
								if kernValue > 10000:
									kernValue = 0
					
					transform = NSAffineTransform.transform()
					transform.translateXBy_yBy_(advance, 0)
					layerPath.transformUsingAffineTransform_( transform )
					advance += layer.width + kernValue
					
					fullPath.appendBezierPath_(layerPath)
		except StandardError:
			print(traceback.format_exc())
		
		if fullPath is None:
			return
		
		try:
			sSum = 0
			upm = float(font.upm)
			for i, s in enumerate(sizes):
				sSum += s + s/4
				transform = NSAffineTransform.transform()
				transform.scaleBy_(s/upm)
				transform.translateXBy_yBy_(tab*upm/s, (h-s-sSum)*upm/s)
				self.drawText(str(s), self.wrapper._foreColour, 10, h-s-sSum-2)
				fullPath.transformUsingAffineTransform_(transform)
				fullPath.fill()
				transform.invert()
				fullPath.transformUsingAffineTransform_(transform)
		except StandardError:
			print(traceback.format_exc())

	def drawText(self, text, textColour, x, y):
		paragraphStyle = NSMutableParagraphStyle.alloc().init()
		paragraphStyle.setAlignment_(1) ## 0=L, 1=R, 2=C, 3=justified
		attributes = {}
		attributes[NSFontAttributeName] = NSFont.systemFontOfSize_(9)
		attributes[NSForegroundColorAttributeName] = textColour
		attributes[NSParagraphStyleAttributeName] = paragraphStyle
		String = NSAttributedString.alloc().initWithString_attributes_(text, attributes)
		String.drawAtPoint_((x, y))


class TheView(VanillaBaseObject):
	nsGlyphPreviewClass = WaterfallView

	def __init__(self, posSize):
		self._glyphsList = []
		self._foreColour = None
		self._backColour = None
		self._instanceIndex = 0
		self._setupView(self.nsGlyphPreviewClass, posSize)
		self._nsObject.wrapper = self

	def redraw(self):
		self._nsObject.setNeedsDisplay_(True)


class WaterfallWindow(GeneralPlugin):
	def settings(self):
		self.name = Glyphs.localize({'en': u'Waterfall', 'de': u'Wasserfall', 'ko': u'폭포형태로 보기'})
		Glyphs.registerDefaults({"com.Tosche.Waterfall.foreColour": [0, 0, 0, 1], "com.Tosche.Waterfall.backColour": [1, 1, 1, 1]})

	## creates Vanilla Window
	#------------------------

	def showWindow(self, sender):
		try:
			edY = 22
			clX = 22
			spX = 8
			spY = 8
			btnY = 17
			self.windowWidth = 300
			self.windowHeight = 240
			self.currentDocument = Glyphs.currentDocument
			self.thisfont = Glyphs.font
			# self.thisfont = GlyphsApp.currentFont()
			self.w = FloatingWindow((self.windowWidth, self.windowWidth), self.name,
				autosaveName = "com.Tosche.Waterfall.mainwindow",
				minSize=(self.windowWidth, self.windowWidth+20))
			self.w.bind("close", self.windowClosed)
			insList = [i.name for i in Glyphs.font.instances]
			insList.insert(0, 'Current Master')
			self.w.edit = EditText( (spX, spY, (-spX*3-clX*2)-80, edY), text="The quick brown jumps over the lazy dog.", callback=self.textChanged)
			self.w.edit.getNSTextField().setNeedsDisplay_(True)
			self.w.edit.getNSTextField().setNeedsLayout_(True)
			self.w.foreColour = ColorWell((-spX*2-clX*2, spY, clX, edY), callback=self.uiChange)
			self.w.backColour = ColorWell((-spX-clX, spY, clX, edY), callback=self.uiChange)
			self.w.refresh = Button((-spX-138, spY, 80, edY), "Refresh", callback=self.textChanged)
			self.w.instancePopup = PopUpButton((spX, spY*2+edY, -spX, edY), insList, callback=self.changeInstance)
			self.w.preview = TheView((0, spX*3+edY*2, -0, -0))
			self.w.preview.instances = {}
			self.loadPrefs()
			self.w.open()
			self.uiChange(None)
			self.changeInstance(self.w.instancePopup)
			self.textChanged(self.w.edit)
			Glyphs.addCallback(self.changeInstance, UPDATEINTERFACE)  # will be called on every change to the interface
			Glyphs.addCallback(self.changeDocument, DOCUMENTACTIVATED)
		except:
			print(traceback.format_exc())

	def loadPrefs(self):
		try:
			editText = Glyphs.defaults["com.Tosche.Waterfall.edit"]
			if editText:
				self.w.edit.set(editText)
			R_f, G_f, B_f, A_f = Glyphs.defaults["com.Tosche.Waterfall.foreColour"]
			self.w.foreColour.set(NSColor.colorWithCalibratedRed_green_blue_alpha_(float(R_f), float(G_f), float(B_f), float(A_f)))
			R_b, G_b, B_b, A_b = Glyphs.defaults["com.Tosche.Waterfall.backColour"]
			self.w.backColour.set(NSColor.colorWithCalibratedRed_green_blue_alpha_(float(R_b), float(G_b), float(B_b), float(A_b)))
		except StandardError:
			print(traceback.format_exc())

	def makeList(self, string):
		try:
			newList = [c for c in string.encode('utf-8', 'surrogatepass').decode('utf-8', 'replace')]
			# print(newList)
			if newList:
				filtered = []
				skip = 0
				for i, c in enumerate(newList):
					if i < skip:
						continue
					if surrogate_start.match(c):
						codepoint = surrogate_pairs.findall(c+newList[i+1])[0]
						# skip over emoji skin tone modifiers
						if codepoint in [u'🏻', u'🏼', u'🏽', u'🏾', u'🏿']:
							continue
						filtered.append(codepoint)
					elif surrogate_start.match(newList[i-1]):
						continue
					elif emoji_variation_selector.match(newList[i]):
						continue
					else:
						if c == "/":
							if i+1 > len(newList)-1:
								filtered.append(c)
								continue
							j = i
							longest = ''.join(newList[i+1:])
							while True:
								if Glyphs.font.glyphs[longest]:
									filtered.append(longest)
									skip = j + len(longest) + 1
									break
								longest = longest[:-1]
								if len(longest) <= 1:
									break
						else:
							filtered.append(c)
				if filtered:
					return filtered
		except StandardError:
			print("Waterfall Error (makeList)", traceback.format_exc())
			Glyphs.showMacroWindow()

	def textChanged(self, sender):
		self.w.preview._glyphsList = self.makeList(self.w.edit.get())
		self.w.preview.redraw()

	def uiChange(self, sender):
		try:
			NSC_f = self.w.foreColour.get()
			R_f, G_f, B_f, A_f = NSC_f.redComponent(), NSC_f.greenComponent(), NSC_f.blueComponent(), NSC_f.alphaComponent()
			NSC_b = self.w.backColour.get()
			R_b, G_b, B_b, A_b = NSC_b.redComponent(), NSC_b.greenComponent(), NSC_b.blueComponent(), NSC_b.alphaComponent()
			self.w.preview._foreColour = NSC_f
			self.w.preview._backColour = NSC_b
			self.w.preview.redraw()
			try:
				Glyphs.defaults["com.Tosche.Waterfall.foreColour"] = (str(R_f), str(G_f), str(B_f), str(A_f))
				Glyphs.defaults["com.Tosche.Waterfall.backColour"] = (str(R_b), str(G_b), str(B_b), str(A_b))
			except AttributeError:
				print(traceback.format_exc())
		except StandardError:
			print(traceback.format_exc())

	def changeDocument(self, sender):
		"""
		Update when current document changes (choosing another open Font)
		"""
		self.w.preview.instances = {}
		self.w.instancePopup.setItems([])
		self.w.preview._instanceIndex = 0
		self.w.preview.redraw()
		self.changeInstance(self.w.instancePopup)
		self.textChanged(None)

	def changeInstance(self, sender):
		currentIndex = self.w.instancePopup.get()
		insList = [i.name for i in Glyphs.font.instances]
		insList.insert(0, 'Current Master')
		if insList != self.w.instancePopup.getItems():
			self.w.instancePopup.setItems(insList)
			currentIndex = 0
		self.w.preview._instanceIndex = currentIndex
		self.w.preview.redraw()

	def start(self):
		newMenuItem = NSMenuItem(self.name, self.showWindow)
		Glyphs.menu[WINDOW_MENU].append(newMenuItem)

	def setWindowController_(self, windowController):
		try:
			self._windowController = windowController
		except:
			self.logError(traceback.format_exc())

	def windowClosed(self, sender):
		Glyphs.defaults["com.Tosche.Waterfall.edit"] = self.w.edit.get()

	def __del__(self):
		Glyphs.removeCallback(self.changeInstance, UPDATEINTERFACE)
		Glyphs.removeCallback(self.changeDocument, DOCUMENTACTIVATED)

	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__