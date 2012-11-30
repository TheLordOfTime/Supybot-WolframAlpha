# -*- coding: utf-8 -*- 
###
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

import urllib2
import urllib
import string
import unicodedata
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.ElementTree as ElementTree

# supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('WolframAlpha')

@internationalizeDocstring
class WolframAlpha(callbacks.Plugin):
    """Add the help for "@plugin help WolframAlpha" here
    This should describe *how* to use this plugin."""
    threaded = True
    
    #def _reencode(self, input_string, decoder = 'utf-8', encoder = 'utf=8'):   
    #    try:
    #        output_string = unicodedata.normalize('NFD', input_string.decode(decoder)).encode(encoder)
    #    except UnicodeError:
    #        output_string = unicodedata.normalize('NFD', input_string.decode('ascii', 'replace')).encode(encoder)
    #    return output_string
    
    # http://products.wolframalpha.com/api/documentation.html
    def wolframalpha(self, irc, msg, args, optlist, optinput):
        """[--options] <input>
        Returns answer from Wolfram Alpha API based on input.
        Ex: freezing point of water at 20,000ft
        """
        
        # check for API key before we can do anything.
        apiKey = self.registryValue('apiKey')
        if not apiKey or apiKey == "Not set":
            irc.reply("Wolfram Alpha API key not set. see 'config help supybot.plugins.WolframAlpha.apiKey'.")
            return
        
        # first, url arguments, some of which getopts and config variables can manipulate.
        urlArgs = { 'input':optinput, 'appid':apiKey, 'reinterpret':'false', 'format':'plaintext', 'units':'nonmetric' }
        
        # args we use internally to control output.                          
        args = { 'maxoutput': self.registryValue('maxOutput'), 'shortest':None, 'fulloutput':None }
        
        # handle getopts.
        if optlist:
            for (key, value) in optlist:
                if key == 'shortest':
                    args['shortest'] = True
                if key == 'fulloutput':
                    args['fulloutput'] = True
                if key == 'lines':
                    args['maxoutput'] == value
                if key == 'usemetric':
                    urlArgs['units'] = 'metric'
                if key == 'reinterpret':
                    urlArgs['reinterpret'] = 'true'
                
        # build url.
        url = 'http://api.wolframalpha.com/v2/query?' + urllib.urlencode(urlArgs)
        self.log.info(url)
                    
        # try and query.                        
        try: 
            #request = urllib2.Request(url, headers={"Accept" : "application/xml"})
            request = urllib2.Request(url)
            u = urllib2.urlopen(request)
        except:
            irc.reply("Failed to load url: %s" % url)
            return

        # now try to process XML.
        tree = ElementTree.parse(u)
        document = tree.getroot()

        # check if we have an error
        if document.attrib['success'] == 'false' or document.attrib['error'] == 'true':
            self.log.debug("ERROR processing input: {0}. Document: {1}".format(optinput, str(document)))
            irc.reply("Something went wrong processing request for: {0}".format(optinput))
            return
        
        # error = false but success = false
        # <didyoumeans>
        #   <didyoumeans count='1'>
        #   <didyoumean>frances split</didyoumean>
        # </didyoumeans>
        #   <futuretopic topic='Operating Systems'
        # msg='Development of this topic is under investigation...' />
        

        # possible_questions = ('Input interpretation', 'Input')
        # possible_answers = ('Current result', 'Response', 'Result', 'Results')
        # title == 'Solution' or title == 'Derivative':  title == "Exact result" or title == "Decimal approximation"):

        # now process the output. We put everything in a dict to process easier later on.
        output = {}
        for pod in document.findall('.//pod'):
            title = pod.attrib['title'].encode('utf-8')
            for plaintext in pod.findall('.//plaintext'):
                if plaintext.text:
                    appendtext = plaintext.text.encode('ascii', 'ignore').replace('\n',' ')
                    output.setdefault(title, []).append(appendtext) 

        if len(output) < 1:
            irc.reply("Something went wrong looking up: {0}".format(optinput))
            return
        else:
            if args['shortest']: # just show the question and answer. 
                irc.reply("{0} :: {1}".format(string.join([item for item in output.get('Input interpretation', None)]), string.join([item for item in output.get('Result', None)])))
            elif args['fulloutput']: # show everything. no limits.
                for i,each in output.iteritems():
                    irc.reply("{0} :: {1}".format(i, string.join([item for item in each], " | ")))
            else:
                for q, (i,each) in enumerate(output.iteritems()):
                    if q < args['maxoutput']:
                        irc.reply("{0} :: {1}".format(i, string.join([item for item in each], " | ")))
                    
    wolframalpha = wrap(wolframalpha, [getopts({'lines':'int',
                                                'reinterpret':'',
                                                'usemetric':'',
                                                'shortest':'',
                                                'fulloutput':''
                                                            }), 'text'])


Class = WolframAlpha


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
