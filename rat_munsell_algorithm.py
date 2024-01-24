# -*- coding: utf-8 -*-

"""
/***************************************************************************
 RatMunsellRgb
                                 A QGIS plugin
 This plugin converts Munsell color system code into RBG value.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-04-14
        copyright            : (C) 2022 by Matjaž Mori
        email                : matjaz.mori@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Matjaž Mori'
__date__ = '2022-04-14'
__copyright__ = '(C) 2022 by Matjaž Mori'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import (QgsProcessing,
                       edit,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProject,
                       QgsField
                       )

import subprocess
import re
try:
    import colour
except:
    subprocess.check_call(['python', '-m', 'pip', 'install', 'colour-science'])
    import colour


class RatMunsellRgbAlgorithm(QgsProcessingAlgorithm):

    INPUT = 'INPUT'

    def initAlgorithm(self, config):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVector]
            )
        )

        self.addParameter(
            QgsProcessingParameterField(
                'field', 
                'Field with Munsell code to convert', 
                type=QgsProcessingParameterField.String, 
                parentLayerParameterName=self.INPUT, 
                allowMultiple=False, 
                defaultValue=None
            )
        )



    def processAlgorithm(self, parameters, context, feedback):
        layer_id = parameters[self.INPUT]  
        input_field = parameters['field']
        layer = QgsProject.instance().mapLayer(layer_id)


        def munsell2rgb(input_value,field_name):
            pattern = r'^(\d+(?:\.\d+)?)([a-zA-Z]+)\s*(\d+)/(\d+)$'
            match = re.match(pattern, input_value)
            hue, prefix, value, chroma = match.groups()
            muns_input = str(hue) + prefix + ' ' + str(value) + '/' + str(chroma)

            xyY = colour.munsell_colour_to_xyY(muns_input)
            XYZ = colour.xyY_to_XYZ(xyY)  

            rgb = colour.XYZ_to_sRGB(XYZ)
            rgb = [max(0, min(1, v)) for v in rgb]
            rgb_255 = [round(v * 255) for v in rgb]
            value = ", ".join(str(e) for e in rgb_255)

            
            field_idx = layer.fields().indexOf(field_name)
            layer.changeAttributeValue(feature.id(), field_idx, value)
         

        total = 100.0 / layer.featureCount() if layer.featureCount() else 0
        with edit(layer):
            field_name = 'srgb'           
            if field_name not in [field.name() for field in layer.fields()]:
                new_field = QgsField(field_name, QVariant.String) 
                layer.dataProvider().addAttributes([new_field])
                layer.updateFields()

            for current, feature in enumerate(layer.getFeatures()):
                input_value = str(feature[input_field])
                feature_id = str(feature.id())
                if input_value:
                    input_value = input_value.strip()
                    if re.match(r'^\d+(\.\d+)?[a-zA-Z]+\s*\d+/\d+$', input_value):
                        munsell2rgb(input_value,field_name)
                        feedback.pushInfo(f"Valid Munsell code detected for feature {feature_id}: {input_value}")
                    else: 
                        feedback.reportError(f"No valid Munsell code detected for feature {feature_id}: {input_value}")
                if feedback.isCanceled():
                    break
                feedback.setProgress(int(current * total))
        return {}
        

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'munsellrgb'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return RatMunsellRgbAlgorithm()
    
    def shortHelpString(self):
        string = """Tool accepts field with munsell codes converts them to sRGB. It is space and case insensitive.
        Iz creates new column named srgb, if it exists already, it will rewrite it.

        Conversion is made using Colour, an open-source Python package:
        https://colour.readthedocs.io/en/develop/index.html#
        
        
        """
        return self.tr(string)
