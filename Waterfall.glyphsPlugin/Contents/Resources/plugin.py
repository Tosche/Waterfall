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

from GlyphsApp.plugins import *
from vanilla import *
from AppKit import NSAffineTransform, NSRectFill, NSView, NSNoBorder, NSColor, NSBezierPath
from Foundation import NSWidth, NSHeight, NSMidX, NSMidY
import traceback
import re

## Viewer class that contains the copied glyph
#------------------------

class WaterfallView(NSView):
	def drawRect_(self, rect):
		try:
			self.wrapper._backColour.set()
		except:
			NSColor.whiteColor().set()
		NSBezierPath.fillRect_(rect)
		sizes = [8, 9, 10, 11, 12, 13, 14, 16, 18, 20, 24, 28, 32, 36, 48, 60, 72, 90, 120]
		lineSpace = 8
		tab = 30
		w = NSWidth(self.frame())
		h = NSHeight(self.frame())
		gs = self.wrapper._glyphsList
		insIndex = self.wrapper._instanceIndex
		if insIndex == 0:
			f = Glyphs.font
			m = f.selectedFontMaster
		else:
			f = Glyphs.font.instances[insIndex-1].interpolatedFont
			m = f.masters[0]
		fullPath = NSBezierPath.alloc().init()
		advance = 0
		try:
			self.wrapper._foreColour.set()
		except:
			NSColor.blackColor().set()
		try:
			for i, g in enumerate(gs):
				if f.glyphs[g]:
					gl = f.glyphs[g].layers[m.id]
					fullPath.appendBezierPath_(gl.completeBezierPath)
					# kerning check
					if i+1 < len(gs) and f.glyphs[gs[i+1]]:
						klg = None
						kli = f.glyphs[g].id
						krg = None
						kri = f.glyphs[gs[i+1]].id
						if f.glyphs[g].rightKerningGroup:
							klg = "@MMK_L_"+f.glyphs[g].rightKerningGroup
						if f.glyphs[gs[i+1]].leftKerningGroup:
							krg = "@MMK_R_"+f.glyphs[gs[i+1]].leftKerningGroup
						try:
							kernValue = f.kerning[m.id][klg][krg]
							try:
								kernValue = f.kerning[m.id][kli][krg]
							except:
								pass
							try:
								kernValue = f.kerning[m.id][klg][kri]
							except:
								pass
							try:
								kernValue = f.kerning[m.id][kli][kri]
							except:
								pass
						except:
							kernValue = 0
					else:
						kernValue = 0
					advance += gl.width + kernValue
					transform = NSAffineTransform.transform()
					transform.translateXBy_yBy_(-gl.width-kernValue, 0)
					fullPath.transformUsingAffineTransform_( transform )
			transform = NSAffineTransform.transform()
			transform.translateXBy_yBy_(advance, 0)
			fullPath.transformUsingAffineTransform_( transform )
		except:
			print traceback.format_exc()
		
		if fullPath is None:
			return
		
		try:
			sSum = 0
			upm = float(f.upm)
			for i, s in enumerate(sizes):
				sSum += s
				transform = NSAffineTransform.transform()
				transform.scaleBy_( s/upm )
				transform.translateXBy_yBy_(tab*upm/s, (h-lineSpace*(i+1)-sSum)*upm/s)
				self.drawText(str(s), self.wrapper._foreColour, 10, h-lineSpace*(i+1)-sSum-2)
				fullPath.transformUsingAffineTransform_( transform )
				fullPath.fill()
				transform.invert()
				fullPath.transformUsingAffineTransform_( transform )
		except:
			print traceback.format_exc()

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
		self._glyphsList = ["T", "h", "e", "space", "q", "u", "i", "c", "k", "space", "b", "r", "o", "w", "n", "space", "j", "u", "m", "p", "s", "space", "o", "v", "e", "r", "space", "t", "h", "e", "space", "l", "a", "z", "y", "space", "d", "o", "g", "period"]
		self._foreColour = NSColor.blackColor()
		self._backColour = NSColor.whiteColor()
		self._instanceIndex = 0
		self._setupView(self.nsGlyphPreviewClass, posSize)
		self._nsObject.wrapper = self
	def redraw(self):
		self._nsObject.setNeedsDisplay_(True)

class WaterfallWindow(GeneralPlugin):
	def settings(self):
		self.name = "Waterfall"

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
			
			self.w = FloatingWindow((self.windowWidth, self.windowWidth), "Waterfall",
				autosaveName = "com.Tosche.Waterfall.mainwindow",
				minSize=(self.windowWidth, self.windowWidth+20))
			insList = [i.name for i in Glyphs.font.instances]
			insList.insert(0, 'Current Master')
			self.w.edit = EditText( (spX, spY, -spX*3-clX*2, edY), text="The quick brown jumps over the lazy dog.", callback=self.uiChange)			
			self.w.foreColour = ColorWell((-spX*2-clX*2, spY, clX, edY), color=NSColor.colorWithCalibratedRed_green_blue_alpha_( 0, 0, 0, 1 ), callback=self.uiChange)
			self.w.backColour = ColorWell((-spX-clX, spY, clX, edY), color=NSColor.colorWithCalibratedRed_green_blue_alpha_( 1, 1, 1, 1 ), callback=self.uiChange)
			self.w.instances = PopUpButton((spX, spY*2+edY, -spX, edY), insList, callback=self.changeGlyph )
			self.w.preview = TheView((0, spX*3+edY*2, -0, -0))
		
			self.loadPrefs()
			self.w.open()
			self.uiChange(self)
			self.changeGlyph(None)
			Glyphs.addCallback( self.changeGlyph, UPDATEINTERFACE ) #will be called on ever change to the interface
		except:
			print traceback.format_exc()

	def loadPrefs(self):
		try:
			if Glyphs.defaults["com.Tosche.Waterfall.edit"] != None:
				self.w.edit.set(Glyphs.defaults["com.Tosche.Waterfall.edit"])
			R_f, G_f, B_f, A_f = Glyphs.defaults["com.Tosche.Waterfall.foreColour"]
			self.w.foreColour.set(NSColor.colorWithCalibratedRed_green_blue_alpha_(float(R_f), float(G_f), float(B_f), float(A_f)))
			R_b, G_b, B_b, A_b = Glyphs.defaults["com.Tosche.Waterfall.backColour"]
			self.w.backColour.set(NSColor.colorWithCalibratedRed_green_blue_alpha_(float(R_b), float(G_b), float(B_b), float(A_b)))
		except:
			pass

	def makeList(self, string):
		try:
			newList=[]
			while string !="":
				if string[0] == "/":
					name = ""
					while string != "" or (string[0] != "/" and string[0] !=" "):
						name = name + string[0]
						if string != "":
							try:
								string = string[1:]
							except:
								pass
						if string =="" or string[0] == "/":
							break
						elif string[0] == " ":
							string = string[1:]
							break
					newList.append(re.sub('/','',name))
				else:
					newList.append(string[0])
					string = string[1:]
			return newList
		except Exception, e:
			Glyphs.showMacroWindow()
			print "Waterfall Error (makeList): %s" % e

	def uiChange(self, sender):
		try:
			self.w.preview._glyphsList = self.makeList(self.w.edit.get())
			NSC_f = self.w.foreColour.get()
			R_f, G_f, B_f, A_f = NSC_f.redComponent(), NSC_f.greenComponent(), NSC_f.blueComponent(), NSC_f.alphaComponent()
			NSC_b = self.w.backColour.get()
			R_b, G_b, B_b, A_b = NSC_b.redComponent(), NSC_b.greenComponent(), NSC_b.blueComponent(), NSC_b.alphaComponent()
			self.w.preview._foreColour = NSC_f
			self.w.preview._backColour = NSC_b
			self.w.preview.redraw()
			try:
				Glyphs.defaults["com.Tosche.Waterfall.edit"] = self.w.edit.get()
				Glyphs.defaults["com.Tosche.Waterfall.foreColour"] = (str(R_f), str(G_f), str(B_f), str(A_f))
				Glyphs.defaults["com.Tosche.Waterfall.backColour"] = (str(R_b), str(G_b), str(B_b), str(A_b))
			except:
				pass
		except:
			pass

	def changeGlyph(self, sender):
		currentIndex = self.w.instances.get()
		insList = [i.name for i in Glyphs.font.instances]
		insList.insert(0, 'Current Master')
		if insList != self.w.instances.getItems():
			self.w.instances.setItems(insList)
			currentIndex = 0
		self.w.preview._instanceIndex = currentIndex
		currentIndex = self.w.instances.get()
		self.w.preview.redraw()

	def start(self):
		newMenuItem = NSMenuItem(self.name, self.showWindow)
		Glyphs.menu[WINDOW_MENU].append(newMenuItem)

	def __del__(self):
		Glyphs.removeCallback( self.changeGlyph, UPDATEINTERFACE )

	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__