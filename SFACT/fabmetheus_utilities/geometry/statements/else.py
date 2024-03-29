"""
Polygon path.

"""

from __future__ import absolute_import
#Init has to be imported first because it has code to workaround the python bug where relative imports don't work if the module is imported as a main module.
import __init__

from fabmetheus_utilities.geometry.geometry_utilities import evaluate


__author__ = 'Enrique Perez (perez_enrique@yahoo.com)'
__credits__ = 'Art of Illusion <http://www.artofillusion.org/>'
__date__ = '$Date: 2008/02/05 $'
__license__ = 'GNU Affero General Public License http://www.gnu.org/licenses/agpl.html'


def processElse(xmlElement):
	"Process the else statement."
	functions = xmlElement.getXMLProcessor().functions
	if len(functions) < 1:
		print('Warning, "else" element is not in a function in processElse in else.py for:')
		print(xmlElement)
		return
	functions[-1].processChildNodes(xmlElement)

def processXMLElement(xmlElement):
	"Process the xml element."
	pass
