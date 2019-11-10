import sys
import PyQt5.QtCore as core
import PyQt5.QtWidgets as widgets
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from lxml import etree
from xml.dom import minidom
from pathlib import Path
import PyQt5.QtGui as gui
import PyQt5.uic as uic
import datetime
import json
import requests
import traceback
import configparser

overpass_url = "http://overpass-api.de/api/interpreter"
gpxcreator = "Overpass Api 2 GPX-Creator (OA2GPX)"
wptsrc = "OpenStreetmap Overpass Api"
gpxfilename = ""

app = widgets.QApplication(sys.argv)
w = uic.loadUi("ui/overpassMainWindow.ui")


def buildgpx(data):
    gpxlink = w.lineEditdefgpxwebsite.text()

    gpxauthor = w.lineEditAuthor.text()
    if gpxauthor == "":
        gpxauthor = "null"

    gpxcopyright = w.lineEditCopyright.text()
    if gpxcopyright == "":
        gpxcopyright = "null"

    generated_on = str(datetime.datetime.now())

    gpxdescription = w.lineEditgpxdescription.text()
    if gpxdescription == "":
        gpxdescription = "null"

    aktuell = 0

    anzahl = len(data['elements'])
    w.progressBarWriteGPX.setFormat('Erzeuge GPX-File: %p%')
    w.progressBarWriteGPX.setMaximum(anzahl)

    root = Element('gpx')
    root.set('version', '1.1')
    root.set('creator', gpxcreator)
    root.set('xmlns', 'http://www.topografix.com/GPX/1/1')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:schemaLocation', 'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd')
    root.set('xmlns:gpx_style', 'http://www.topografix.com/GPX/gpx_style/0/2')

    metadata = SubElement(root, 'metadata')

    name = SubElement(metadata, 'name')
    name.text = gpxfilename

    description = SubElement(metadata, 'desc')
    description.text = gpxdescription

    author = SubElement(metadata, 'author')
    author.text = gpxauthor

    metacopyright = SubElement(metadata, 'copyright')
    metacopyright.text = gpxcopyright

    link = SubElement(metadata, 'link')
    link.text = gpxlink

    time = SubElement(metadata, 'time')
    time.text = generated_on

    for element in data['elements']:
        aktuell += 1
        name = ""
        desc = "OSM Tags:\nType: {0}\nId: {1}\n".format(element['type'], element['id'])

        website = "null"

        ref = "null"

        if element['type'] == 'node':
            lon = element['lon']
            lat = element['lat']

        elif 'center' in element:
            lon = element['center']['lon']
            lat = element['center']['lat']

        if 'tags' in element:
            for tag in element['tags']:
                desc += "{0}: {1}\n".format(tag, element['tags'][tag])
                if tag == "ref":
                    ref = element['tags']['ref']
                if tag == "website":
                    website = element['tags']['website']
                if tag == 'name':
                    name = element['tags']['name']

        wpt_grp = SubElement(root, 'wpt')
        wpt_grp.set('lat', str(lat))
        wpt_grp.set('lon', str(lon))

        if name != "":
            wpt_info_cmt = SubElement(wpt_grp, 'cmt')
            wpt_info_cmt.text = name

        wpt_info_src = SubElement(wpt_grp, 'src')
        wpt_info_src.text = wptsrc

        wpt_info_type = SubElement(wpt_grp, 'type')
        wpt_info_type.text = 'POI'

        wpt_info_ele = SubElement(wpt_grp, 'ele')
        wpt_info_ele.text = '500'

        wpt_info_time = SubElement(wpt_grp, 'time')
        wpt_info_time.text = generated_on

        wpt_info_name = SubElement(wpt_grp, 'name')
        wpt_info_name.text = ref

        wpt_info_desc = SubElement(wpt_grp, 'desc')
        wpt_info_desc.text = desc

        wpt_info_link = SubElement(wpt_grp, 'link')
        wpt_info_link.text = website

        wpt_info_sym = SubElement(wpt_grp, 'sym')
        wpt_info_sym.text = 'Flag, Blue'

        w.progressBarWriteGPX.setValue(aktuell)

    gpxstring = minidom.parseString(tostring(root,
                                             encoding="utf-8",
                                             method="xml")).toprettyxml(indent="   ",
                                                                        encoding="utf-8")

    return gpxstring


def writegpx(gpxstring, outfile):
    try:

        with open(outfile, "wb+") as f:
            f.write(gpxstring)
            f.close()
        return True

    except Exception:
        traceback.print_exc()
        return False


def outputselect():
    global gpxfilename
    gpxfilename = widgets.QFileDialog.getSaveFileName(w, "Ausgabe speichern unter",
                                                      "unbenannt.gpx",
                                                      "GPX-Datei (*.gpx);;"
                                                      "Alle Dateien (*.*)")[0]
    if gpxfilename != "":
        if not (gpxfilename.endswith(".gpx")):
            gpxfilename += '.gpx'
        w.labelAusgabedatei.setText(str(gpxfilename))
        w.statusbar.showMessage('Save as: {0}'.format(gpxfilename))
    else:
        print('Es wurde keine Datei ausgewählt!')
        w.statusbar.showMessage('Es wurde keine Datei ausgewählt')


def overpassabfrage():
    w.progressBarWriteGPX.setValue(0)
    charformat = w.textEditAbfrage.currentCharFormat()
    query = w.textEditAbfrage.toPlainText()

    # print(query)
    try:
        response = requests.get(overpass_url, params={'data': query})
        data = response.json()
    except Exception:
        traceback.print_exc()
        w.statusbar.showMessage('ERROR: Abfrage konnte nicht durchgeführt werden.')
        return False

    if writegpx(buildgpx(data), gpxfilename):
        print("Datei geschrieben")
        w.statusbar.showMessage('GPX-Datei erfolgreich geschrieben')
    else:
        w.statusbar.showMessage('GPX-Datei konnte nicht geschrieben werden.')
        print("Datei konnte nicht geschrieben werden")


def saveconfig():
    configfilename = widgets.QFileDialog.getSaveFileName(w, "Config speichern unter",
                                                         "unbenannt.o2g",
                                                         "Overpass Api 2 GPX-Creator (OA2GPX) Config (*.o2g);;"
                                                         "Alle Dateien (*.*)")[0]
    if configfilename != "":
        if not (configfilename.endswith(".o2g")):
            configfilename += '.o2g'
    else:
        print('Es wurde keine Datei ausgewählt!')
        w.statusbar.showMessage('Es wurde keine Datei ausgewählt')

    config = configparser.ConfigParser()
    config['DEFAULT'] = {}
    config['gpx'] = {}
    config['gpx']['file'] = gpxfilename
    config['gpx']['author'] = w.lineEditAuthor.text()
    config['gpx']['description'] = w.lineEditgpxdescription.text()
    config['gpx']['copyright'] = w.lineEditCopyright.text()
    config['gpx']['website'] = w.lineEditdefgpxwebsite.text()
    config['overpass'] = {}
    config['overpass']['query'] = str(w.textEditAbfrage.toPlainText())

    if writeconfig(config, configfilename):
        w.statusbar.showMessage('Config erfolgreich gespeichert')
    else:
        w.statusbar.showMessage('ERROR: Config konnte nicht gespeichert werden!')


def writeconfig(config, filename):
    try:
        with open(filename, 'w+') as configfile:
            config.write(configfile)
        return True
    except Exception:
        traceback.print_exc()
        return False


def openconfig():
    global gpxfilename
    configfilename = widgets.QFileDialog.getOpenFileName(w, "Config laden", "", "Overpass Api 2 GPX-Creator (OA2GPX) Config (*.o2g)")[0]

    config = configparser.ConfigParser()
    try:
        config.read(configfilename)
        gpxfilename = config['gpx']['file']
        w.labelAusgabedatei.setText(config['gpx']['file'])
        w.lineEditAuthor.setText(config['gpx']['author'])
        w.lineEditgpxdescription.setText(config['gpx']['description'])
        w.lineEditCopyright.setText(config['gpx']['copyright'])
        w.lineEditdefgpxwebsite.setText(config['gpx']['website'])
        w.textEditAbfrage.setPlainText(str(config['overpass']['query']))
        w.statusbar.showMessage("Config geladen")
    except Exception:
        traceback.print_exc()
        w.statusbar.showMessage("ERROR: Config konnte nicht geladen werden.")


# if not (gpxfilename):
# w.pushButtonAbfrage.setEnabled(False)


w.pushButtonAbfrage.clicked.connect(overpassabfrage)
w.pushButtonDateiauswahl.clicked.connect(outputselect)

w.actionSpeichern.triggered.connect(saveconfig)
w.actionOeffnen.triggered.connect(openconfig)

w.show()
sys.exit(app.exec_())
