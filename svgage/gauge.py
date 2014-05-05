# -*- coding: utf-8 -*-
from __future__ import (print_function, division, absolute_import, unicode_literals)

import cairosvg
import re
import math

from svgwrite import Drawing
from svgwrite.path import Path


class Gauge(object):
    config = {
        'id'                    : None,
        'title'                 : 'Title',
        'titleFontColor'        : '#999999',
        'value'                 : 0,
        'valueFontColor'        : '#010101',
        'min'                   : 0,
        'max'                   : 100,
        'showMinMax'            : True,
        'gaugeWidthScale'       : 1.0,
        'gaugeColor'            : '#edebeb',
        'label'                 : "",
        'showInnerShadow'       : True,
        'shadowOpacity'         : 0.2,
        'shadowSize'            : 5,
        'shadowVerticalOffset'  : 3,
        'levelColors'           : ["#a9d70b", "#f9c802", "#ff0000"],
        'levelColorsGradient'   : True,
        'labelFontColor'        : "#b3b3b3",
        'showNeedle'            : False,
        'needleColor'           : "#b3b3b3",
        'canvasWidth'           : 400,
        'canvasHeight'          : 300,
    }

    def __init__(self, *args, **kwargs):
        for param_name, param_value in kwargs.items():
            if self.config.has_key(param_name):
                self.config[param_name] = param_value

        # Overflow values
        if self.config['value'] > self.config['max']:
            self.config['value'] = self.config['max']
        if self.config['value'] < self.config['min']:
            self.config['value'] = self.config['min']
        self.originalValue = self.config['value']

        self.canvas = Drawing(size=(self.config['canvasWidth'],
                                    self.config['canvasHeight']))

        canvasW = self.config['canvasWidth']
        canvasH = self.config['canvasHeight']

        self.canvas.add(self.canvas.rect(insert=(0, 0),
                                         size=(canvasW, canvasH),
                                         stroke="none",
                                         fill="#ffffff"))

        # widget dimensions
        widgetW, widgetH = None, None
        if ((canvasW / canvasH) > 1.25):
            widgetW = 1.25 * canvasH
            widgetH = canvasH
        else:
            widgetW = canvasW
            widgetH = canvasW / 1.25

        # delta 
        dx = (canvasW - widgetW)/2
        dy = (canvasH - widgetH)/2

        # title 
        titleFontSize = ((widgetH / 8) > 10) and (widgetH / 10) or 10
        titleX = dx + widgetW / 2
        titleY = dy + widgetH / 6.5

        # value 
        valueFontSize = ((widgetH / 6.4) > 16) and (widgetH / 6.4) or 16
        valueX = dx + widgetW / 2
        valueY = dy + widgetH / 1.4

        # label 
        labelFontSize = ((widgetH / 16) > 10) and (widgetH / 16) or 10
        labelX = dx + widgetW / 2
        labelY = valueY + valueFontSize / 2 + 6

        # min 
        minFontSize = ((widgetH / 16) > 10) and (widgetH / 16) or 10
        minX = dx + (widgetW / 10) + (widgetW / 6.666666666666667 * self.config['gaugeWidthScale']) / 2
        minY = dy + widgetH / 1.126760563380282

        # max
        maxFontSize = ((widgetH / 16) > 10) and (widgetH / 16) or 10
        maxX = dx + widgetW - (widgetW / 10) - (widgetW / 6.666666666666667 * self.config['gaugeWidthScale']) / 2
        maxY = dy + widgetH / 1.126760563380282

        # parameters
        self.params = {
            'canvasW'         : canvasW,
            'canvasH'         : canvasH,
            'widgetW'         : widgetW,
            'widgetH'         : widgetH,
            'dx'              : dx,
            'dy'              : dy,
            'titleFontSize'   : titleFontSize,
            'titleX'          : titleX,
            'titleY'          : titleY,
            'valueFontSize'   : valueFontSize,
            'valueX'          : valueX,
            'valueY'          : valueY,
            'labelFontSize'   : labelFontSize,
            'labelX'          : labelX,
            'labelY'          : labelY,
            'minFontSize'     : minFontSize,
            'minX'            : minX,
            'minY'            : minY,
            'maxFontSize'     : maxFontSize,
            'maxX'            : maxX,
            'maxY'            : maxY
        }

        # gauge
        self.gauge = self.gauge_path(self.config['max'], self.config['min'], self.config['max'],
                                     self.params['widgetW'], self.params['widgetH'], self.params['dx'],
                                     self.params['dy'], self.config['gaugeWidthScale'],
                                     stroke='none',
                                     fill=self.config['gaugeColor'])

        self.canvas.add(self.gauge)

        # level
        percent_value = (self.config['value'] - self.config['min']) / (self.config['max'] - self.config['min'])
        self.level = self.gauge_path(self.config['value'], self.config['min'], self.config['max'],
                                     self.params['widgetW'], self.params['widgetH'], self.params['dx'],
                                     self.params['dy'], self.config['gaugeWidthScale'],
                                     stroke='none',
                                     fill=self.get_color_for_value(percent_value,
                                                                   self.config['levelColors'],
                                                                   self.config['levelColorsGradient']))
        self.canvas.add(self.level)

        # needle
        if self.config['showNeedle']:
            self.needle = self.needle_path(self.config['value'], self.config['min'], self.config['max'],
                                           self.params['widgetW'], self.params['widgetH'], self.params['dx'],
                                           self.params['dy'], self.config['gaugeWidthScale'],
                                           stroke='none',
                                           fill=self.config['needleColor'])
            self.canvas.add(self.needle)

        # Value
        else:
            text_config = {
                "font-size"     : "%d" % self.params['valueFontSize'],
                "font-weight"   : "bold",
                "font-family"   : "Arial",
                "fill"          : self.config['valueFontColor'],
                "fill-opacity"  : "1",
                "text-anchor"  : 'middle'
            }
            value_text = self.canvas.text('',
                                          insert=('%d' % self.params['valueX'],
                                                  '%d' % self.params['valueY']),
                                          **text_config)
            value_tspan = self.canvas.tspan(self.originalValue,
                                            dy=[8])
            value_text.add(value_tspan)
            self.canvas.add(value_text)

        # Add min & max value
        self.show_minmax()


    def save(self, path):
        svg = self.canvas.tostring()
        svg2png = getattr(cairosvg, 'svg2png')
        png_byte = svg2png(bytestring=svg)
        f = open(path,'w')
        f.write(png_byte)
        f.close()


    def gauge_path(self, value, val_min, val_max, w, h, dx, dy, gws, **extra):
        alpha = (1 - (value - val_min) / (val_max - val_min)) * math.pi
        Ro = w / 2 - w / 10
        Ri = Ro - w / 6.666666666666667 * gws
        Cx = w / 2 + dx
        Cy = h / 1.25 + dy

        Xo = w / 2 + dx + Ro * math.cos(alpha)
        Yo = h - (h - Cy) + dy - Ro * math.sin(alpha)
        Xi = w / 2 + dx + Ri * math.cos(alpha)
        Yi = h - (h - Cy) + dy - Ri * math.sin(alpha)

        path = []
        path.append(u"M%d,%d " % ((Cx - Ri), Cy))
        path.append(u"L%d,%d " % ((Cx - Ro), Cy))
        path.append(u"A%d,%d 0 0,1 %d,%d " % (Ro, Ro, Xo, Yo))
        path.append(u"L%d,%d " % (Xi, Yi))
        path.append(u"A%d,%d 0 0,0 %d,%d " % (Ri, Ri, (Cx - Ri), Cy))
        path.append(u"z ")

        return Path(d=path, **extra)

    def needle_path(self, value, val_min, val_max, w, h, dx, dy, gws, **extra):
        xO = w / 2 + dx
        yO = h / 1.25 + dy

        Rext = w / 2 - w / 10
        Rint = Rext - w / 6.666666666666667 * gws

        x_offset = xO
        y_offset = h - (h - yO) + dy

        val = (value - val_min) / (val_max - val_min)

        angle_b = val<0.5 and val*math.pi or (math.pi - val*math.pi) # Angle de la pointe
        angle_a = math.pi/2 - angle_b
        angle_c = math.pi/2 - angle_b

        rayon_base = 7
        rayon_b = Rint + (Rext-Rint)*10/100

        xA = x_offset + -1 * rayon_base * math.cos(angle_a)
        yA = y_offset - (val<0.5 and -1 or 1) * rayon_base * math.sin(angle_a)

        xC = x_offset + 1 * rayon_base * math.cos(angle_c)
        yC = y_offset - (val<0.5 and 1 or -1) * rayon_base * math.sin(angle_c)

        xB = x_offset + (val<0.5 and -1 or 1) * rayon_b * math.cos(angle_b)
        yB = y_offset - rayon_b * math.sin(angle_b)

        path = []
        path.append(u"M%d,%d " % (xA, yA))
        path.append(u"L%d,%d " % (xB, yB))
        path.append(u"L%d,%d " % (xC, yC))
        path.append(u"A%d,%d 0 1,1 %d,%d " % (rayon_base, rayon_base, xA, yA))
        path.append(u"z ")

        return Path(d=path, **extra)

    def get_color_for_value(self, pct, color, grad):
        no = len(color);
        if no == 1: return color[0]

        HEX = r'[a-fA-F\d]{2}'
        HEX_COLOR = r'#(?P<red>%(hex)s)(?P<green>%(hex)s)(?P<blue>%(hex)s)' % {'hex': HEX}
        inc = grad and (1 / (no - 1)) or (1 / no)
        colors = []
        i = 0
        while i < no:
            percentage = (grad) and (inc * i) or (inc * (i + 1))
            parts = re.match(HEX_COLOR,color[i]).groupdict()

            rval = int(parts['red'], 16)
            gval = int(parts['green'], 16)
            bval = int(parts['blue'], 16)
            colors.append({
                'pct': percentage,
                'color': {
                    'r': rval,
                    'g': gval,
                    'b': bval
                 }
            })
            i+=1

        if pct == 0:
            return 'rgb(%d,%d,%d)' % (colors[0]['color']['r'],
                                      colors[0]['color']['g'],
                                      colors[0]['color']['b'])

        i = 0
        while i < len(colors):
            if pct <= colors[i]['pct']:
                if (grad == True):
                    lower = colors[i-1]
                    upper = colors[i]
                    _range = upper['pct'] - lower['pct']
                    rangePct = (pct - lower['pct']) / _range
                    pctLower = 1 - rangePct
                    pctUpper = rangePct
                    color = {
                      'r': math.floor(lower['color']['r'] * pctLower + upper['color']['r'] * pctUpper),
                      'g': math.floor(lower['color']['g'] * pctLower + upper['color']['g'] * pctUpper),
                      'b': math.floor(lower['color']['b'] * pctLower + upper['color']['b'] * pctUpper)
                    }
                    return 'rgb(%d,%d,%d)' % (color['r'], color['g'], color['b'])
                else:
                    return 'rgb(%d,%d,%d)' % (colors[i]['color']['r'],
                                              colors[i]['color']['g'],
                                              colors[i]['color']['b']) 
            i+=1

    def show_minmax(self):
        # min
        txtMin_config = {
            "font-size"    : '%d' % self.params['minFontSize'],
            "font-weight"  : "normal",
            "font-family"  : "Arial",
            "fill"         : self.config['labelFontColor'],
            "fill-opacity" : self.config['showMinMax'] and "1" or "0",
            "text-anchor"  : 'middle'
        }
        txtMin = self.canvas.text(self.config['min'],
                                  insert=(self.params['minX'],
                                          self.params['minY']),
                                  **txtMin_config)

        self.canvas.add(txtMin)

        # max
        txtMax_config = {
            "font-size"    : '%d' % self.params['maxFontSize'],
            "font-weight"  :"normal",
            "font-family"  :"Arial",
            "fill"         : self.config['labelFontColor'],   
            "fill-opacity" : self.config['showMinMax'] and "1" or "0",
            "text-anchor"  : 'middle'
        }
        txtMax = self.canvas.text(self.config['max'],
                                  insert=(self.params['maxX'],
                                          self.params['maxY']),
                                  **txtMax_config)
        self.canvas.add(txtMax)

#
testGauge = Gauge(canvasWidth=202.5,
                  canvasHeight=115,
                  value=40,
                  valueFontColor="#2c5aa1",
                  gaugeColor="#d1d2d4",
                  gaugeWidthScale=0.8,
                  levelColors=["#d7423a", "#e4bd20", "#799f3f"],
                  levelColorsGradient=False,
                  showNeedle=False,
                  needleColor="#2c5aa1")
# python -c 'from oqs.mopa.core.svg.gauge import testGauge; testGauge.save(path="/tmp/test.png")' && eog /tmp/test.png